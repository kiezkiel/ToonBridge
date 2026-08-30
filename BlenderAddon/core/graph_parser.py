"""
ToonBridge Graph Parser
Serializes Blender ShaderNodeTree into a clean, platform-agnostic Intermediate Representation (IR).
"""

from typing import Dict, Any, List, Optional, Tuple


class ToonBridgeGraphParser:
    """Traverses and converts Blender ShaderNodeTree into ToonBridge IR JSON structure."""

    MATH_OPERATION_MAP = {
        'ADD': 'ADD',
        'SUBTRACT': 'SUBTRACT',
        'MULTIPLY': 'MULTIPLY',
        'DIVIDE': 'DIVIDE',
        'MULTIPLY_ADD': 'MULTIPLY_ADD',
        'POWER': 'POWER',
        'LOGARITHM': 'LOGARITHM',
        'SQRT': 'SQRT',
        'INVERSE_SQRT': 'INVERSE_SQRT',
        'ABSOLUTE': 'ABS',
        'EXPONENT': 'EXP',
        'MINIMUM': 'MIN',
        'MAXIMUM': 'MAX',
        'LESS_THAN': 'LESS_THAN',
        'GREATER_THAN': 'GREATER_THAN',
        'SIGN': 'SIGN',
        'ROUND': 'ROUND',
        'FLOOR': 'FLOOR',
        'CEIL': 'CEIL',
        'TRUNC': 'TRUNC',
        'FRACT': 'FRAC',
        'MODULO': 'MODULO',
        'PINGPONG': 'PINGPONG',
        'SINE': 'SINE',
        'COSINE': 'COSINE',
        'TANGENT': 'TANGENT',
        'ARCSINE': 'ASIN',
        'ARCCOSINE': 'ACOS',
        'ARCTANGENT': 'ATAN',
        'ATAN2': 'ATAN2',
        'SMOOTH_MIN': 'SMOOTH_MIN',
        'SMOOTH_MAX': 'SMOOTH_MAX',
    }

    VECTOR_MATH_OPERATION_MAP = {
        'ADD': 'VEC_ADD',
        'SUBTRACT': 'VEC_SUBTRACT',
        'MULTIPLY': 'VEC_MULTIPLY',
        'DIVIDE': 'VEC_DIVIDE',
        'CROSS_PRODUCT': 'CROSS_PRODUCT',
        'DOT_PRODUCT': 'DOT_PRODUCT',
        'DISTANCE': 'DISTANCE',
        'LENGTH': 'LENGTH',
        'SCALE': 'SCALE',
        'NORMALIZE': 'NORMALIZE',
        'ABSOLUTE': 'VEC_ABS',
        'MINIMUM': 'VEC_MIN',
        'MAXIMUM': 'VEC_MAX',
        'FLOOR': 'VEC_FLOOR',
        'CEIL': 'VEC_CEIL',
        'FRACTION': 'VEC_FRAC',
        'MODULO': 'VEC_MODULO',
        'WRAP': 'VEC_WRAP',
        'SNAP': 'VEC_SNAP',
        'SINE': 'VEC_SINE',
        'COSINE': 'VEC_COSINE',
        'TANGENT': 'VEC_TANGENT',
        'PROJECT': 'PROJECT',
        'REFLECT': 'REFLECT',
        'REFRACT': 'REFRACT',
        'FACEFORWARD': 'FACEFORWARD',
    }

    PROCEDURAL_TYPES = {
        'ShaderNodeTexNoise',
        'ShaderNodeTexVoronoi',
        'ShaderNodeTexMusgrave',
        'ShaderNodeTexWave',
        'ShaderNodeTexMagic',
        'ShaderNodeTexChecker',
        'ShaderNodeTexBrick',
        'ShaderNodeTexGradient',
    }

    def __init__(self, node_tree=None):
        self.node_tree = node_tree
        self.parsed_nodes: Dict[str, Dict[str, Any]] = {}
        self.connections: List[Dict[str, Any]] = []
        self.cel_shading_chains: List[Dict[str, Any]] = []
        self.procedural_nodes: List[Dict[str, Any]] = []
        self.color_ramps: List[Dict[str, Any]] = []
        self.material_output_id: Optional[str] = None

    def parse(self) -> Dict[str, Any]:
        """Traverse the node tree and return complete intermediate manifest."""
        if not self.node_tree:
            return {"error": "No node tree provided"}

        nodes = self.node_tree.nodes
        links = self.node_tree.links

        # 1. Find the active Material Output node
        output_node = self._find_active_output_node(nodes)
        if output_node:
            self.material_output_id = output_node.name

        # 2. Parse all nodes
        for node in nodes:
            parsed = self._parse_single_node(node)
            if parsed:
                self.parsed_nodes[node.name] = parsed

        # 3. Parse all links (connections)
        for link in links:
            if not link.is_valid:
                continue
            conn = {
                "from_node": link.from_node.name,
                "from_socket": link.from_socket.name,
                "from_socket_index": self._get_socket_index(link.from_node.outputs, link.from_socket),
                "to_node": link.to_node.name,
                "to_socket": link.to_socket.name,
                "to_socket_index": self._get_socket_index(link.to_node.inputs, link.to_socket),
            }
            self.connections.append(conn)

        # 4. Identify stylized & cel-shading sub-graphs
        self._detect_stylized_chains()

        return {
            "version": "1.0.0",
            "material_name": getattr(self.node_tree, "name", "UnnamedMaterial"),
            "output_node_id": self.material_output_id,
            "nodes": self.parsed_nodes,
            "connections": self.connections,
            "cel_chains": self.cel_shading_chains,
            "procedural_nodes": self.procedural_nodes,
            "color_ramps": self.color_ramps,
        }

    def _find_active_output_node(self, nodes):
        for node in nodes:
            if node.bl_idname == 'ShaderNodeOutputMaterial' and getattr(node, 'is_active_output', True):
                return node
        # Fallback to any output node
        for node in nodes:
            if node.bl_idname == 'ShaderNodeOutputMaterial':
                return node
        return None

    def _get_socket_index(self, sockets, target_socket) -> int:
        for idx, s in enumerate(sockets):
            if s == target_socket:
                return idx
        return 0

    def _parse_single_node(self, node) -> Optional[Dict[str, Any]]:
        bl_type = node.bl_idname
        node_info: Dict[str, Any] = {
            "id": node.name,
            "label": getattr(node, "label", "") or node.name,
            "blender_type": bl_type,
            "location": [float(node.location.x), float(node.location.y)],
            "inputs": self._parse_node_inputs(node),
            "outputs": self._parse_node_outputs(node),
            "attributes": {},
        }

        if bl_type == 'ShaderNodeMath':
            op = getattr(node, 'operation', 'ADD')
            node_info["ir_type"] = "MATH"
            node_info["attributes"]["operation"] = self.MATH_OPERATION_MAP.get(op, op)
            node_info["attributes"]["use_clamp"] = getattr(node, 'use_clamp', False)

        elif bl_type == 'ShaderNodeVectorMath':
            op = getattr(node, 'operation', 'ADD')
            node_info["ir_type"] = "VECTOR_MATH"
            node_info["attributes"]["operation"] = self.VECTOR_MATH_OPERATION_MAP.get(op, op)

        elif bl_type == 'ShaderNodeMix':
            node_info["ir_type"] = "MIX"
            node_info["attributes"]["data_type"] = getattr(node, 'data_type', 'RGBA')
            node_info["attributes"]["blend_type"] = getattr(node, 'blend_type', 'MIX')
            node_info["attributes"]["clamp_result"] = getattr(node, 'clamp_result', False)

        elif bl_type == 'ShaderNodeMixRGB':
            node_info["ir_type"] = "MIX"
            node_info["attributes"]["data_type"] = 'RGBA'
            node_info["attributes"]["blend_type"] = getattr(node, 'blend_type', 'MIX')
            node_info["attributes"]["use_clamp"] = getattr(node, 'use_clamp', False)

        elif bl_type == 'ShaderNodeMapRange':
            node_info["ir_type"] = "MAP_RANGE"
            node_info["attributes"]["interpolation_type"] = getattr(node, 'interpolation_type', 'LINEAR')
            node_info["attributes"]["clamp"] = getattr(node, 'clamp', True)

        elif bl_type == 'ShaderNodeValToRGB':
            node_info["ir_type"] = "COLOR_RAMP"
            ramp_data = self._extract_color_ramp_data(node)
            node_info["attributes"]["color_ramp"] = ramp_data
            self.color_ramps.append({"node_id": node.name, "data": ramp_data})

        elif bl_type == 'ShaderNodeShaderToRGB':
            node_info["ir_type"] = "SHADER_TO_RGB"

        elif bl_type in self.PROCEDURAL_TYPES:
            node_info["ir_type"] = "PROCEDURAL_NOISE"
            node_info["attributes"]["noise_subtype"] = bl_type
            self.procedural_nodes.append({"node_id": node.name, "type": bl_type})

        elif bl_type == 'ShaderNodeTexImage':
            node_info["ir_type"] = "TEXTURE_SAMPLE"
            image = getattr(node, 'image', None)
            node_info["attributes"]["image_name"] = image.name if image else ""
            node_info["attributes"]["filepath"] = image.filepath if image else ""
            node_info["attributes"]["color_space"] = getattr(image, 'colorspace_settings', None).name if image and hasattr(image, 'colorspace_settings') else 'sRGB'

        elif bl_type == 'ShaderNodeTexCoord':
            node_info["ir_type"] = "TEXTURE_COORDINATE"

        elif bl_type == 'ShaderNodeMapping':
            node_info["ir_type"] = "MAPPING"
            node_info["attributes"]["vector_type"] = getattr(node, 'vector_type', 'POINT')

        elif bl_type in ('ShaderNodeSeparateXYZ', 'ShaderNodeSeparateColor', 'ShaderNodeSeparateRGB'):
            node_info["ir_type"] = "SEPARATE_CHANNELS"

        elif bl_type in ('ShaderNodeCombineXYZ', 'ShaderNodeCombineColor', 'ShaderNodeCombineRGB'):
            node_info["ir_type"] = "COMBINE_CHANNELS"

        elif bl_type == 'ShaderNodeValue':
            node_info["ir_type"] = "CONSTANT_FLOAT"
            outputs = node.outputs
            node_info["attributes"]["value"] = float(outputs[0].default_value) if outputs else 0.0

        elif bl_type == 'ShaderNodeRGB':
            node_info["ir_type"] = "CONSTANT_COLOR"
            outputs = node.outputs
            col = outputs[0].default_value if outputs else [1.0, 1.0, 1.0, 1.0]
            node_info["attributes"]["color"] = [float(c) for c in col]

        elif bl_type == 'ShaderNodeInvert':
            node_info["ir_type"] = "INVERT"

        elif bl_type == 'ShaderNodeClamp':
            node_info["ir_type"] = "CLAMP"

        elif bl_type == 'ShaderNodeBsdfDiffuse':
            node_info["ir_type"] = "BSDF_DIFFUSE"

        elif bl_type == 'ShaderNodeBsdfPrincipled':
            node_info["ir_type"] = "BSDF_PRINCIPLED"

        elif bl_type == 'ShaderNodeEmission':
            node_info["ir_type"] = "EMISSION"

        elif bl_type == 'ShaderNodeOutputMaterial':
            node_info["ir_type"] = "MATERIAL_OUTPUT"

        else:
            node_info["ir_type"] = "GENERIC_NODE"

        return node_info

    def _parse_node_inputs(self, node) -> List[Dict[str, Any]]:
        inputs_list = []
        for idx, inp in enumerate(node.inputs):
            val = None
            if hasattr(inp, 'default_value'):
                dv = inp.default_value
                if hasattr(dv, '__iter__') and not isinstance(dv, str):
                    val = [float(v) for v in dv]
                elif isinstance(dv, (int, float)):
                    val = float(dv)
                elif isinstance(dv, str):
                    val = str(dv)
            inputs_list.append({
                "index": idx,
                "name": inp.name,
                "type": inp.type,
                "default_value": val,
            })
        return inputs_list

    def _parse_node_outputs(self, node) -> List[Dict[str, Any]]:
        outputs_list = []
        for idx, out in enumerate(node.outputs):
            outputs_list.append({
                "index": idx,
                "name": out.name,
                "type": out.type,
            })
        return outputs_list

    def _extract_color_ramp_data(self, node) -> Dict[str, Any]:
        color_ramp = node.color_ramp
        stops = []
        for element in color_ramp.elements:
            stops.append({
                "position": float(element.position),
                "color": [float(c) for c in element.color],
            })
        return {
            "interpolation": color_ramp.interpolation,
            "stops": stops,
            "total_stops": len(stops),
        }

    def _detect_stylized_chains(self):
        """Identifies patterns like [Diffuse BSDF] -> [Shader to RGB] -> [ColorRamp] (Cel-Shading)."""
        shader_to_rgb_nodes = [
            nid for nid, n in self.parsed_nodes.items()
            if n.get("ir_type") == "SHADER_TO_RGB"
        ]

        for s2rgb_id in shader_to_rgb_nodes:
            # Find downstream ColorRamp
            downstream_ramps = []
            for conn in self.connections:
                if conn["from_node"] == s2rgb_id:
                    target = self.parsed_nodes.get(conn["to_node"])
                    if target and target.get("ir_type") == "COLOR_RAMP":
                        downstream_ramps.append(target)

            self.cel_shading_chains.append({
                "shader_to_rgb_node": s2rgb_id,
                "downstream_color_ramps": [r["id"] for r in downstream_ramps],
                "type": "EEVEE_CEL_SHADING",
            })
