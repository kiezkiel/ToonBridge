"""
ToonBridge Procedural Noise Baker
Detects non-transferable procedural texture subtrees and bakes them to seamless image maps.
"""

import os
from typing import List, Dict, Any, Optional


class ProceduralNoiseBaker:
    """Automates isolation and baking of Blender procedural textures into 2K/4K image maps."""

    PROCEDURAL_TYPES = {
        'ShaderNodeTexNoise',
        'ShaderNodeTexVoronoi',
        'ShaderNodeTexMusgrave',
        'ShaderNodeTexWave',
        'ShaderNodeTexMagic',
        'ShaderNodeTexChecker',
        'ShaderNodeTexBrick',
    }

    def __init__(self, context=None, resolution: int = 2048):
        self.context = context
        self.resolution = resolution

    def find_procedural_nodes(self, material) -> List[Any]:
        """Finds all procedural texture nodes in the material node tree."""
        if not material or not material.use_nodes or not material.node_tree:
            return []

        procedural_nodes = []
        for node in material.node_tree.nodes:
            if node.bl_idname in self.PROCEDURAL_TYPES:
                procedural_nodes.append(node)
        return procedural_nodes

    def bake_procedural_node(
        self,
        obj,
        material,
        noise_node,
        output_dir: str,
        filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Temporarily isolates the procedural node through an Emission shader and bakes to PNG.
        Returns the absolute filepath of the baked image.
        """
        try:
            import bpy
        except ImportError:
            print("[ToonBridge] Headless environment detected: skipping live bpy bake.")
            return None

        if not filename:
            safe_node_name = noise_node.name.replace(" ", "_").replace(".", "_")
            filename = f"T_{material.name}_{safe_node_name}_Baked.png"

        output_path = os.path.join(output_dir, filename)

        tree = material.node_tree
        nodes = tree.nodes
        links = tree.links

        # 1. Create temporary bake target image
        bake_img = bpy.data.images.new(
            name=f"TB_Bake_{noise_node.name}",
            width=self.resolution,
            height=self.resolution,
            alpha=True,
            float_buffer=False
        )

        # 2. Add temporary Image Texture node
        img_node = nodes.new('ShaderNodeTexImage')
        img_node.image = bake_img
        img_node.select = True
        nodes.active = img_node

        # 3. Add temporary Emission shader
        emission_node = nodes.new('ShaderNodeEmission')
        output_node = None
        for n in nodes:
            if n.bl_idname == 'ShaderNodeOutputMaterial' and getattr(n, 'is_active_output', True):
                output_node = n
                break

        if not output_node:
            output_node = nodes.new('ShaderNodeOutputMaterial')

        # Store original output link
        original_surface_link = None
        if output_node.inputs['Surface'].is_linked:
            original_surface_link = output_node.inputs['Surface'].links[0]
            from_socket = original_surface_link.from_socket

        # Connect noise node output (Color or Fac) -> Emission -> Surface
        noise_output = noise_node.outputs.get('Color') or noise_node.outputs.get('Fac') or noise_node.outputs[0]
        links.new(noise_output, emission_node.inputs['Color'])
        links.new(emission_node.outputs['Emission'], output_node.inputs['Surface'])

        # 4. Configure render engine for bake
        scene = self.context.scene if self.context else bpy.context.scene
        orig_engine = scene.render.engine
        scene.render.engine = 'CYCLES'
        scene.cycles.bake_type = 'EMIT'
        scene.cycles.samples = 1  # 1 sample is sufficient for deterministic procedural noise

        try:
            # Execute bake
            bpy.ops.object.bake(type='EMIT')
            bake_img.filepath_raw = output_path
            bake_img.file_format = 'PNG'
            bake_img.save()
            print(f"[ToonBridge] Successfully baked procedural node to: {output_path}")
        except Exception as e:
            print(f"[ToonBridge] Bake failed: {e}")
            output_path = None
        finally:
            # 5. Cleanup temporary nodes and restore original links
            nodes.remove(img_node)
            nodes.remove(emission_node)
            if original_surface_link and from_socket:
                links.new(from_socket, output_node.inputs['Surface'])
            scene.render.engine = orig_engine
            bpy.data.images.remove(bake_img)

        return output_path
