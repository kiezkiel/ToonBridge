"""
ToonBridge Node Factory (Unreal Engine 5)
Instantiates and configures Unreal Material Expressions corresponding to Blender Intermediate Representation (IR).
"""

from typing import Dict, Any, Optional

try:
    import unreal
except ImportError:
    unreal = None


class ToonBridgeNodeFactory:
    """Creates and connects Material Expressions inside Unreal Engine Materials."""

    @staticmethod
    def create_expression(material, node_info: Dict[str, Any], imported_textures: Dict[str, Any] = None):
        """Instantiates the appropriate MaterialExpression for the given node info."""
        if not unreal or not material:
            return None

        ir_type = node_info.get("ir_type", "GENERIC_NODE")
        attrs = node_info.get("attributes", {})
        loc = node_info.get("location", [0.0, 0.0])
        node_x = int(loc[0])
        node_y = int(-loc[1])  # Invert Y to match Unreal's coordinate space

        expr = None

        if ir_type == "MATH":
            op = attrs.get("operation", "ADD")
            if op == "ADD":
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionAdd, node_x, node_y)
            elif op == "SUBTRACT":
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionSubtract, node_x, node_y)
            elif op == "MULTIPLY":
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionMultiply, node_x, node_y)
            elif op == "DIVIDE":
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionDivide, node_x, node_y)
            elif op == "POWER":
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionPower, node_x, node_y)
            elif op == "ABS":
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionAbs, node_x, node_y)
            elif op == "MIN":
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionMin, node_x, node_y)
            elif op == "MAX":
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionMax, node_x, node_y)
            elif op == "FRAC":
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionFrac, node_x, node_y)
            elif op == "FLOOR":
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionFloor, node_x, node_y)
            elif op == "CEIL":
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionCeil, node_x, node_y)
            elif op == "SINE":
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionSine, node_x, node_y)
            elif op == "COSINE":
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionCosine, node_x, node_y)
            elif op == "SQRT":
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionSquareRoot, node_x, node_y)
            else:
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionAdd, node_x, node_y)

        elif ir_type == "VECTOR_MATH":
            op = attrs.get("operation", "DOT_PRODUCT")
            if op == "DOT_PRODUCT":
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionDotProduct, node_x, node_y)
            elif op == "CROSS_PRODUCT":
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionCrossProduct, node_x, node_y)
            elif op == "NORMALIZE":
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionNormalize, node_x, node_y)
            elif op == "VEC_ADD":
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionAdd, node_x, node_y)
            elif op == "VEC_MULTIPLY":
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionMultiply, node_x, node_y)
            elif op == "VEC_SUBTRACT":
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionSubtract, node_x, node_y)
            else:
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionDotProduct, node_x, node_y)

        elif ir_type in ("MIX", "MIX_SHADER"):
            # Linear Interpolation (Lerp)
            expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionLinearInterpolate, node_x, node_y)

        elif ir_type == "MAP_RANGE":
            # Map Range linear fallback
            expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionLinearInterpolate, node_x, node_y)

        elif ir_type == "FRESNEL":
            expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionFresnel, node_x, node_y)
            if expr:
                expr.set_editor_property("exponent", 3.0)

        elif ir_type == "GEOMETRY":
            expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionPixelNormalWS, node_x, node_y)

        elif ir_type == "BSDF_TRANSPARENT":
            expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant, node_x, node_y)
            if expr:
                expr.set_editor_property("r", 0.0)

        elif ir_type == "SEPARATE_CHANNELS":
            expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionComponentMask, node_x, node_y)
            if expr:
                expr.set_editor_property("r", False)
                expr.set_editor_property("g", True)
                expr.set_editor_property("b", False)
                expr.set_editor_property("a", False)

        elif ir_type == "COMBINE_CHANNELS":
            expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionAppendVector, node_x, node_y)

        elif ir_type == "CONSTANT_FLOAT":
            expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionScalarParameter, node_x, node_y)
            if expr:
                clean_param_name = node_info.get("id", "ScalarParam").replace(" ", "_").replace(".", "_")
                expr.set_editor_property("parameter_name", clean_param_name)
                expr.set_editor_property("default_value", float(attrs.get("value", 1.0)))

        elif ir_type == "CONSTANT_COLOR":
            expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionVectorParameter, node_x, node_y)
            if expr:
                clean_param_name = node_info.get("id", "ColorParam").replace(" ", "_").replace(".", "_")
                expr.set_editor_property("parameter_name", clean_param_name)
                col = attrs.get("color", [1.0, 1.0, 1.0, 1.0])
                linear_color = unreal.LinearColor(col[0], col[1], col[2], col[3] if len(col) > 3 else 1.0)
                expr.set_editor_property("default_value", linear_color)

        elif ir_type == "TEXTURE_COORDINATE":
            expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionTextureCoordinate, node_x, node_y)

        elif ir_type in ("TEXTURE_SAMPLE", "PROCEDURAL_NOISE"):
            node_id = node_info.get("id")
            clean_id = node_id.replace(" ", "_").replace(".", "_") if node_id else ""
            tex_asset = None
            if imported_textures:
                tex_asset = imported_textures.get(node_id) or imported_textures.get(clean_id)

            if tex_asset:
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionTextureSample, node_x, node_y)
                if expr:
                    expr.set_editor_property("texture", tex_asset)
            else:
                # Safe fallback: create Constant3Vector instead of an unassigned broken TextureSample
                expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, node_x, node_y)
                if expr:
                    expr.set_editor_property("constant", unreal.LinearColor(0.8, 0.8, 0.8, 1.0))

        elif ir_type == "CLAMP":
            expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionClamp, node_x, node_y)

        elif ir_type == "INVERT":
            expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionOneMinus, node_x, node_y)

        return expr

    @staticmethod
    def connect_pins(from_expr, from_output_name: str, to_expr, to_input_name: str, socket_index: int = 0) -> bool:
        """Connects output of from_expr to input of to_expr in Unreal."""
        if not unreal or not from_expr or not to_expr:
            return False

        try:
            # Match output socket
            out_pin = ""
            if from_output_name in ("A", "Alpha"):
                out_pin = "A"
            elif from_output_name in ("R", "X", "Red"):
                out_pin = "R"
            elif from_output_name in ("G", "Y", "Green"):
                out_pin = "G"
            elif from_output_name in ("B", "Z", "Blue"):
                out_pin = "B"

            # Match input socket
            in_pin = ""
            if to_input_name in ("Alpha", "Fac", "Factor"):
                in_pin = "Alpha"
            elif to_input_name in ("A", "Value1", "Vector1", "Base", "Color1", "Input"):
                in_pin = "A"
            elif to_input_name in ("B", "Value2", "Vector2", "Exp", "Color2"):
                in_pin = "B"
            elif to_input_name == "Shader":
                # For Mix Shader: index 1 is Shader A, index 2 is Shader B
                in_pin = "B" if socket_index >= 2 else "A"
            elif to_input_name in ("UVs", "Coordinates"):
                in_pin = "UVs"

            unreal.MaterialEditingLibrary.connect_material_expressions(
                from_expr, out_pin, to_expr, in_pin
            )
            return True
        except Exception:
            return False
