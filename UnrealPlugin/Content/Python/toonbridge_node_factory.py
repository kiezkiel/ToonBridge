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
        node_y = int(-loc[1])  # Invert Y to match Unreal's graph coordinate space

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

        elif ir_type == "MIX":
            # Linear Interpolation (Lerp)
            expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionLinearInterpolate, node_x, node_y)

        elif ir_type == "CONSTANT_FLOAT":
            expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionScalarParameter, node_x, node_y)
            if expr:
                expr.set_editor_property("parameter_name", node_info.get("id", "ScalarParam"))
                expr.set_editor_property("default_value", attrs.get("value", 1.0))

        elif ir_type == "CONSTANT_COLOR":
            expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionVectorParameter, node_x, node_y)
            if expr:
                expr.set_editor_property("parameter_name", node_info.get("id", "ColorParam"))
                col = attrs.get("color", [1.0, 1.0, 1.0, 1.0])
                linear_color = unreal.LinearColor(col[0], col[1], col[2], col[3] if len(col) > 3 else 1.0)
                expr.set_editor_property("default_value", linear_color)

        elif ir_type == "TEXTURE_COORDINATE":
            expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionTextureCoordinate, node_x, node_y)

        elif ir_type in ("TEXTURE_SAMPLE", "PROCEDURAL_NOISE"):
            expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionTextureSample, node_x, node_y)
            if expr and imported_textures:
                node_id = node_info.get("id")
                tex_asset = imported_textures.get(node_id)
                if tex_asset:
                    expr.set_editor_property("texture", tex_asset)

        elif ir_type == "CLAMP":
            expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionClamp, node_x, node_y)

        elif ir_type == "INVERT":
            expr = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionOneMinus, node_x, node_y)

        return expr

    @staticmethod
    def connect_pins(from_expr, from_output_name: str, to_expr, to_input_name: str) -> bool:
        """Connects output of from_expr to input of to_expr in Unreal."""
        if not unreal or not from_expr or not to_expr:
            return False

        try:
            # Clean socket name matching
            out_pin = ""
            if "Alpha" in from_output_name or from_output_name == "A":
                out_pin = "A"
            elif "Red" in from_output_name or from_output_name == "R":
                out_pin = "R"
            elif "Green" in from_output_name or from_output_name == "G":
                out_pin = "G"
            elif "Blue" in from_output_name or from_output_name == "B":
                out_pin = "B"

            # Input socket matching
            in_pin = ""
            if to_input_name in ("A", "Value1", "Vector1", "Base"):
                in_pin = "A"
            elif to_input_name in ("B", "Value2", "Vector2", "Exp"):
                in_pin = "B"
            elif to_input_name in ("Alpha", "Fac", "Factor"):
                in_pin = "Alpha"

            unreal.MaterialEditingLibrary.connect_material_expressions(
                from_expr, out_pin, to_expr, in_pin
            )
            return True
        except Exception as e:
            print(f"[ToonBridge] Pin connection warning ({from_output_name} -> {to_input_name}): {e}")
            return False
