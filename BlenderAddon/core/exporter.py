"""
ToonBridge Exporter
Bundles serialized material manifest, baked procedural textures, 1D LUTs, and mesh FBX into a .toonbridge container.
"""

import os
import json
import zipfile
import shutil
import tempfile
from typing import Tuple, Dict, Any

from .graph_parser import ToonBridgeGraphParser
from .color_ramp_parser import ColorRampParser
from .noise_baker import ProceduralNoiseBaker


class ToonBridgeExporter:
    """Main export pipeline coordinator."""

    def __init__(self, context=None, settings=None):
        self.context = context
        self.settings = settings

    def export_package(self, obj, material) -> Tuple[bool, str]:
        """Runs the complete export workflow and packages to .toonbridge file."""
        import bpy

        # Create temporary working directory
        temp_dir = tempfile.mkdtemp(prefix="toonbridge_export_")
        textures_dir = os.path.join(temp_dir, "Textures")
        os.makedirs(textures_dir, exist_ok=True)

        package_name = self.settings.package_name if self.settings else "StylizedAsset"
        export_dir = bpy.path.abspath(self.settings.export_path) if self.settings else os.getcwd()
        if not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)

        final_package_path = os.path.join(export_dir, f"{package_name}.toonbridge")

        try:
            # 1. Parse Material Graph
            parser = ToonBridgeGraphParser(material.node_tree)
            manifest = parser.parse()

            # 2. Process ColorRamps & Generate 1D Gradient LUTs
            lut_references = []
            cel_mode = getattr(self.settings, 'cel_mode', 'HYBRID')

            for ramp_entry in manifest.get("color_ramps", []):
                node_id = ramp_entry["node_id"]
                ramp_data = ramp_entry["data"]
                stops = ramp_data.get("stops", [])

                # Always generate clean 1D LUT texture for exact color fidelity
                lut_filename = f"T_LUT_{material.name}_{node_id}.png".replace(" ", "_")
                lut_filepath = os.path.join(textures_dir, lut_filename)
                ColorRampParser.save_lut_png(ramp_data, lut_filepath, width=256)
                lut_references.append({
                    "node_id": node_id,
                    "filename": lut_filename,
                    "relative_path": f"Textures/{lut_filename}",
                })

                # Also store mathematical steps
                ramp_entry["cel_steps"] = ColorRampParser.extract_cel_step_parameters(ramp_data)

            manifest["lut_textures"] = lut_references

            # 3. Bake Procedural Textures
            resolution = int(getattr(self.settings, 'bake_resolution', '2048'))
            baker = ProceduralNoiseBaker(self.context, resolution=resolution)
            procedural_nodes = baker.find_procedural_nodes(material)
            baked_references = []

            for p_node in procedural_nodes:
                baked_file = baker.bake_procedural_node(
                    obj=obj,
                    material=material,
                    noise_node=p_node,
                    output_dir=textures_dir
                )
                if baked_file and os.path.exists(baked_file):
                    rel_name = os.path.basename(baked_file)
                    baked_references.append({
                        "node_id": p_node.name,
                        "filename": rel_name,
                        "relative_path": f"Textures/{rel_name}",
                    })

            manifest["baked_textures"] = baked_references

            # 4. Check for Inverted Hull Outline Modifier
            outline_data = self._extract_outline_modifier(obj)
            manifest["outline_settings"] = outline_data

            # 5. Export Mesh (FBX)
            mesh_filename = None
            if getattr(self.settings, 'export_mesh', True):
                mesh_filename = f"SM_{package_name}.fbx"
                mesh_path = os.path.join(temp_dir, mesh_filename)
                self._export_fbx_mesh(obj, mesh_path)
                manifest["mesh"] = {
                    "filename": mesh_filename,
                    "relative_path": mesh_filename,
                }

            # 6. Write manifest.json
            manifest_path = os.path.join(temp_dir, "manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

            # 7. Compress into .toonbridge package (ZIP archive)
            with zipfile.ZipFile(final_package_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        abs_file = os.path.join(root, file)
                        rel_file = os.path.relpath(abs_file, temp_dir)
                        zf.write(abs_file, rel_file)

            return True, f"Successfully exported ToonBridge package to: {final_package_path}"

        except Exception as e:
            return False, str(e)

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _extract_outline_modifier(self, obj) -> Dict[str, Any]:
        """Detects Solidify outline modifiers on the object."""
        for mod in obj.modifiers:
            if mod.type == 'SOLIDIFY' and getattr(mod, 'use_flip_normals', False):
                return {
                    "has_inverted_hull": True,
                    "thickness": float(mod.thickness),
                    "offset": float(mod.offset),
                    "material_offset": int(getattr(mod, 'material_offset', 1)),
                }
        return {
            "has_inverted_hull": bool(getattr(self.settings, 'auto_outline', False)),
            "thickness": float(getattr(self.settings, 'outline_width', 0.02)),
            "offset": 1.0,
            "material_offset": 1,
        }

    def _export_fbx_mesh(self, obj, output_path: str):
        """Exports the active mesh with split normals for optimal Unreal shading."""
        import bpy

        # Save current selection
        active_obj = bpy.context.view_layer.objects.active
        selected_objs = [o for o in bpy.context.selected_objects]

        # Select only target object
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        bpy.ops.export_scene.fbx(
            filepath=output_path,
            use_selection=True,
            global_scale=1.0,
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_ALL',
            mesh_smooth_type='FACE',
            use_mesh_modifiers=True,
            use_custom_props=True,
            add_leaf_bones=False,
            bake_anim=False,
        )

        # Restore selection
        bpy.ops.object.select_all(action='DESELECT')
        for o in selected_objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = active_obj
