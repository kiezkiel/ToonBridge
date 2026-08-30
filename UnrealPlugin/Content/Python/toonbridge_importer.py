"""
ToonBridge Importer (Unreal Engine 5)
Main orchestrator for importing .toonbridge packages into Unreal Engine 5.
"""

import os
import re
from typing import Dict, Any, Optional

try:
    import unreal
except ImportError:
    unreal = None

try:
    from toonbridge_manifest import ToonBridgePackage
    from toonbridge_node_factory import ToonBridgeNodeFactory
    from toonbridge_cel_builder import ToonBridgeCelBuilder
except (ImportError, ValueError):
    from .toonbridge_manifest import ToonBridgePackage
    from .toonbridge_node_factory import ToonBridgeNodeFactory
    from .toonbridge_cel_builder import ToonBridgeCelBuilder


def sanitize_unreal_name(name: str) -> str:
    """Sanitizes names for Unreal Engine asset naming rules (no spaces, dots, or invalid chars)."""
    clean = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    clean = re.sub(r'_+', '_', clean).strip('_')
    return clean or "Asset"


class ToonBridgeImporter:
    """Imports and reconstructs Blender stylized assets in Unreal Engine 5."""

    def __init__(self, destination_path: str = "/Game/ToonBridge"):
        self.destination_path = destination_path
        self.mesh_path = f"{destination_path}/Meshes"
        self.texture_path = f"{destination_path}/Textures"
        self.material_path = f"{destination_path}/Materials"

    def import_package(self, package_file_path: str) -> bool:
        """Executes the full import and reconstruction pipeline."""
        if not unreal:
            print("[ToonBridge] Error: Unreal Engine Python API is not available in this environment.")
            return False

        pkg = ToonBridgePackage(package_file_path)
        if not pkg.unpack():
            unreal.log_error(f"[ToonBridge] Failed to unpack {package_file_path}")
            return False

        try:
            clean_mat_name = sanitize_unreal_name(pkg.material_name)
            unreal.log(f"[ToonBridge] Starting import for material: {clean_mat_name}")

            # 1. Import Baked Textures & 1D LUTs
            imported_textures = self._import_textures(pkg)

            # 2. Import Mesh FBX
            imported_mesh = self._import_mesh(pkg)

            # 3. Create and Reconstruct Material
            material_asset = self._reconstruct_material(pkg, imported_textures)

            # 4. Assign Material to Static Mesh
            if imported_mesh and material_asset:
                self._assign_material_to_mesh(imported_mesh, material_asset)

            unreal.log(f"[ToonBridge] Successfully imported and reconstructed M_{clean_mat_name}!")
            return True

        except Exception as e:
            unreal.log_error(f"[ToonBridge] Import failed with exception: {e}")
            import traceback
            unreal.log_error(traceback.format_exc())
            return False

        finally:
            pkg.cleanup()

    def _import_textures(self, pkg: ToonBridgePackage) -> Dict[str, Any]:
        """Imports all baked textures and LUT images into the Content Browser."""
        texture_assets = {}
        all_textures = pkg.baked_textures + pkg.lut_textures

        for tex_entry in all_textures:
            node_id = tex_entry.get("node_id")
            rel_path = tex_entry.get("relative_path")
            abs_path = pkg.get_absolute_file_path(rel_path)

            if not os.path.exists(abs_path):
                continue

            raw_name = os.path.splitext(os.path.basename(rel_path))[0]
            asset_name = sanitize_unreal_name(raw_name)

            task = unreal.AssetImportTask()
            task.set_editor_property("filename", abs_path)
            task.set_editor_property("destination_path", self.texture_path)
            task.set_editor_property("destination_name", asset_name)
            task.set_editor_property("replace_existing", True)
            task.set_editor_property("automated", True)
            task.set_editor_property("save", True)

            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            imported_asset = task.get_editor_property("imported_object_paths")
            if imported_asset:
                tex_obj = unreal.EditorAssetLibrary.load_asset(imported_asset[0])
                if "LUT" in asset_name and tex_obj:
                    # Configure LUT Texture settings (Clamp addressing, LinearColor / non-SRGB)
                    try:
                        tex_obj.set_editor_property("srgb", False)
                    except Exception:
                        try:
                            tex_obj.set_editor_property("s_rgb", False)
                        except Exception:
                            pass

                    try:
                        tex_obj.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP)
                        tex_obj.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
                    except Exception:
                        pass

                    try:
                        unreal.EditorAssetLibrary.save_loaded_asset(tex_obj)
                    except Exception:
                        pass

                texture_assets[node_id] = tex_obj

        return texture_assets

    def _import_mesh(self, pkg: ToonBridgePackage) -> Optional[Any]:
        """Imports the FBX mesh asset."""
        mesh_info = pkg.mesh_info
        if not mesh_info:
            return None

        rel_path = mesh_info.get("relative_path")
        abs_path = pkg.get_absolute_file_path(rel_path)
        if not os.path.exists(abs_path):
            return None

        raw_name = os.path.splitext(os.path.basename(rel_path))[0]
        mesh_name = sanitize_unreal_name(raw_name)

        task = unreal.AssetImportTask()
        task.set_editor_property("filename", abs_path)
        task.set_editor_property("destination_path", self.mesh_path)
        task.set_editor_property("destination_name", mesh_name)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("automated", True)
        task.set_editor_property("save", True)

        fbx_options = unreal.FbxImportUI()
        fbx_options.set_editor_property("import_mesh", True)
        fbx_options.set_editor_property("import_textures", False)
        fbx_options.set_editor_property("import_materials", False)
        try:
            fbx_options.static_mesh_import_data.set_editor_property("combine_meshes", True)
            fbx_options.static_mesh_import_data.set_editor_property(
                "normal_import_method", unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
            )
        except Exception:
            pass

        task.set_editor_property("options", fbx_options)

        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        imported_paths = task.get_editor_property("imported_object_paths")
        if imported_paths:
            return unreal.EditorAssetLibrary.load_asset(imported_paths[0])
        return None

    def _reconstruct_material(self, pkg: ToonBridgePackage, imported_textures: Dict[str, Any]):
        """Builds the complete material expression graph."""
        clean_mat_name = sanitize_unreal_name(pkg.material_name)
        mat_name = f"M_{clean_mat_name}"
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

        # Create Material Asset
        material = asset_tools.create_asset(
            mat_name,
            self.material_path,
            unreal.Material,
            unreal.MaterialFactoryNew()
        )

        if not material:
            unreal.log_error(f"[ToonBridge] Could not create material asset: {mat_name}")
            return None

        created_expressions: Dict[str, Any] = {}

        # 1. Instantiate direct nodes (Math, Mix, Vector, Coordinates, Constants)
        for node_id, node_data in pkg.nodes.items():
            ir_type = node_data.get("ir_type")
            if ir_type in ("MATERIAL_OUTPUT", "SHADER_TO_RGB", "COLOR_RAMP"):
                continue

            expr = ToonBridgeNodeFactory.create_expression(material, node_data, imported_textures)
            if expr:
                created_expressions[node_id] = expr

        # 2. Identify Cel-Shading chains vs Standard Gradient ramps
        cel_ramp_ids = set()
        for chain in pkg.manifest.get("cel_chains", []):
            for r_id in chain.get("downstream_color_ramps", []):
                cel_ramp_ids.add(r_id)

        # 3. Instantiate ColorRamp expressions with clean driver inputs
        for ramp_entry in pkg.color_ramps:
            ramp_node_id = ramp_entry["node_id"]
            node_data = pkg.nodes.get(ramp_node_id, {})
            lut_tex = imported_textures.get(ramp_node_id)
            is_cel_lighting = (ramp_node_id in cel_ramp_ids)

            # Find driver connection into this ColorRamp
            driver_expr = None
            driver_sock = ""
            if not is_cel_lighting:
                for conn in pkg.connections:
                    if conn["to_node"] == ramp_node_id and conn["to_socket"] in ("Fac", "Factor", "Value"):
                        driver_id = conn["from_node"]
                        driver_sock = conn["from_socket"]
                        driver_expr = created_expressions.get(driver_id)
                        break

            ramp_expr = ToonBridgeCelBuilder.build_color_ramp_expression(
                material=material,
                node_data=node_data,
                ramp_entry=ramp_entry,
                lut_texture_asset=lut_tex,
                is_cel_lighting_ramp=is_cel_lighting,
                incoming_driver_expr=driver_expr,
                incoming_driver_sock=driver_sock
            )
            if ramp_expr:
                created_expressions[ramp_node_id] = ramp_expr

        # 4. Wire downstream connections (Mix, Multiply, Add, etc.)
        output_node_id = pkg.manifest.get("output_node_id", "Material Output")
        for conn in pkg.connections:
            from_id = conn["from_node"]
            to_id = conn["to_node"]
            from_sock = conn["from_socket"]
            to_sock = conn["to_socket"]

            # Skip output node and ColorRamp Fac links (already handled)
            if to_id == output_node_id:
                continue
            if to_id in pkg.nodes and pkg.nodes[to_id].get("ir_type") == "COLOR_RAMP":
                continue

            from_expr = created_expressions.get(from_id)
            to_expr = created_expressions.get(to_id)
            if from_expr and to_expr:
                ToonBridgeNodeFactory.connect_pins(from_expr, from_sock, to_expr, to_sock)

        # 5. Connect terminal output to Base Color
        terminal_expr = self._resolve_terminal_expression(output_node_id, pkg.connections, created_expressions)
        if terminal_expr:
            try:
                unreal.MaterialEditingLibrary.connect_material_property(
                    terminal_expr, "", unreal.MaterialProperty.MP_BASE_COLOR
                )
            except Exception as e:
                unreal.log_warning(f"[ToonBridge] Base Color connection: {e}")

        # Set Roughness to 1.0 and Specular to 0.0 to eliminate deferred plastic glare
        try:
            const_rough = unreal.MaterialEditingLibrary.create_material_expression(
                material, unreal.MaterialExpressionConstant, -100, 200
            )
            if const_rough:
                const_rough.set_editor_property("r", 1.0)
                unreal.MaterialEditingLibrary.connect_material_property(
                    const_rough, "", unreal.MaterialProperty.MP_ROUGHNESS
                )
        except Exception:
            pass

        # 6. Recompile and save material
        try:
            unreal.MaterialEditingLibrary.recompile_material(material)
        except Exception:
            try:
                unreal.MaterialEditingLibrary.update_material_after_graph_change(material)
            except Exception:
                try:
                    material.post_edit_change()
                except Exception:
                    pass

        try:
            unreal.EditorAssetLibrary.save_loaded_asset(material)
        except Exception:
            pass

        unreal.log(f"[ToonBridge] Reconstructed Material saved to: {self.material_path}/{mat_name}")
        return material

    def _resolve_terminal_expression(self, output_id: str, connections: list, created_expressions: dict):
        """Finds the final shader/color expression that should drive Base Color."""
        # 1. Direct connection to output node
        for conn in connections:
            if conn["to_node"] == output_id:
                from_id = conn["from_node"]
                if from_id in created_expressions:
                    return created_expressions[from_id]

                # Look one level back if connected through a BSDF or Emission node
                for sub in connections:
                    if sub["to_node"] == from_id:
                        sub_from = sub["from_node"]
                        if sub_from in created_expressions:
                            return created_expressions[sub_from]

        # 2. Fallback: Return the last created expression
        for expr in reversed(list(created_expressions.values())):
            if expr:
                return expr

        return None

    def _assign_material_to_mesh(self, mesh_asset, material_asset):
        """Assigns the reconstructed material to the imported Static Mesh."""
        if not mesh_asset or not material_asset:
            return

        try:
            unreal.EditorStaticMeshLibrary.set_material(mesh_asset, 0, material_asset)
            unreal.EditorAssetLibrary.save_loaded_asset(mesh_asset)
            unreal.log(f"[ToonBridge] Assigned material to mesh: {mesh_asset.get_name()}")
            return
        except Exception:
            pass

        try:
            static_materials = mesh_asset.get_editor_property("static_materials")
            if static_materials and len(static_materials) > 0:
                static_materials[0].set_editor_property("material_interface", material_asset)
            else:
                mat_slot = unreal.StaticMaterial()
                mat_slot.set_editor_property("material_interface", material_asset)
                mat_slot.set_editor_property("material_slot_name", "M_Toon")
                mesh_asset.set_editor_property("static_materials", [mat_slot])
            unreal.EditorAssetLibrary.save_loaded_asset(mesh_asset)
            unreal.log(f"[ToonBridge] Assigned material to mesh static_materials.")
        except Exception as e:
            unreal.log_warning(f"[ToonBridge] Note on mesh material assignment: {e}")
