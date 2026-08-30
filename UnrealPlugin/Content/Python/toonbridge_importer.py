"""
ToonBridge Importer (Unreal Engine 5)
Main orchestrator for importing .toonbridge packages into Unreal Engine 5.
"""

import os
from typing import Dict, Any, Optional

try:
    import unreal
except ImportError:
    unreal = None

try:
    from .toonbridge_manifest import ToonBridgePackage
    from .toonbridge_node_factory import ToonBridgeNodeFactory
    from .toonbridge_cel_builder import ToonBridgeCelBuilder
except (ImportError, ValueError):
    from toonbridge_manifest import ToonBridgePackage
    from toonbridge_node_factory import ToonBridgeNodeFactory
    from toonbridge_cel_builder import ToonBridgeCelBuilder


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
            unreal.log(f"[ToonBridge] Starting import for material: {pkg.material_name}")

            # 1. Import Baked Textures & 1D LUTs
            imported_textures = self._import_textures(pkg)

            # 2. Import Mesh FBX
            imported_mesh = self._import_mesh(pkg)

            # 3. Create and Reconstruct Material
            material_asset = self._reconstruct_material(pkg, imported_textures)

            # 4. Assign Material to Static Mesh
            if imported_mesh and material_asset:
                self._assign_material_to_mesh(imported_mesh, material_asset)

            unreal.log(f"[ToonBridge] Successfully imported and reconstructed {pkg.material_name}!")
            return True

        except Exception as e:
            unreal.log_error(f"[ToonBridge] Import failed with exception: {e}")
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

            asset_name = os.path.splitext(os.path.basename(rel_path))[0]

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
                    # Configure LUT Texture settings (Clamp addressing, LinearColor)
                    tex_obj.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP)
                    tex_obj.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
                    tex_obj.set_editor_property("s_rgb", False)
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

        mesh_name = os.path.splitext(os.path.basename(rel_path))[0]

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
        fbx_options.static_mesh_import_data.set_editor_property("combine_meshes", True)
        fbx_options.static_mesh_import_data.set_editor_property(
            "normal_import_method", unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
        )
        task.set_editor_property("options", fbx_options)

        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        imported_paths = task.get_editor_property("imported_object_paths")
        if imported_paths:
            return unreal.EditorAssetLibrary.load_asset(imported_paths[0])
        return None

    def _reconstruct_material(self, pkg: ToonBridgePackage, imported_textures: Dict[str, Any]):
        """Builds the complete material expression graph."""
        mat_name = f"M_{pkg.material_name}"
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

        # Create Material Asset
        material = asset_tools.create_asset(
            mat_name,
            self.material_path,
            unreal.Material,
            unreal.MaterialFactoryNew()
        )

        if not material:
            return None

        created_expressions: Dict[str, Any] = {}

        # 1. Instantiate direct nodes
        for node_id, node_data in pkg.nodes.items():
            ir_type = node_data.get("ir_type")
            if ir_type in ("MATERIAL_OUTPUT", "SHADER_TO_RGB"):
                continue

            expr = ToonBridgeNodeFactory.create_expression(material, node_data, imported_textures)
            if expr:
                created_expressions[node_id] = expr

        # 2. Build Cel-Shading sub-networks for ColorRamps
        for ramp_entry in pkg.color_ramps:
            ramp_node_id = ramp_entry["node_id"]
            lut_tex = imported_textures.get(ramp_node_id)
            cel_expr = ToonBridgeCelBuilder.build_cel_shading_network(
                material=material,
                ramp_entry=ramp_entry,
                lut_texture_asset=lut_tex
            )
            if cel_expr:
                created_expressions[ramp_node_id] = cel_expr

        # 3. Wire all connections
        for conn in pkg.connections:
            from_id = conn["from_node"]
            to_id = conn["to_node"]
            from_sock = conn["from_socket"]
            to_sock = conn["to_socket"]

            # Handle Material Output connection
            if to_id == pkg.manifest.get("output_node_id"):
                final_expr = created_expressions.get(from_id)
                if final_expr:
                    unreal.MaterialEditingLibrary.connect_material_property(
                        final_expr, "", unreal.MaterialProperty.MP_BASE_COLOR
                    )
                continue

            from_expr = created_expressions.get(from_id)
            to_expr = created_expressions.get(to_id)
            if from_expr and to_expr:
                ToonBridgeNodeFactory.connect_pins(from_expr, from_sock, to_expr, to_sock)

        # 4. Compile and update material graph
        unreal.MaterialEditingLibrary.update_material_after_graph_change(material)
        unreal.EditorAssetLibrary.save_loaded_asset(material)
        return material

    def _assign_material_to_mesh(self, mesh_asset, material_asset):
        """Assigns the reconstructed material to the imported Static Mesh."""
        try:
            mesh_asset.set_material(0, material_asset)
            unreal.EditorAssetLibrary.save_loaded_asset(mesh_asset)
        except Exception as e:
            unreal.log_warning(f"[ToonBridge] Could not auto-assign material to mesh: {e}")
