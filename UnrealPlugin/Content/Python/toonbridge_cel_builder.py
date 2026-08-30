"""
ToonBridge ColorRamp & Cel-Shading Builder (Unreal Engine 5)
Constructs clean, non-overlapping ColorRamp LUT sampling and Cel-Shading sub-networks.
"""

from typing import Dict, Any, List, Optional

try:
    import unreal
except ImportError:
    unreal = None


class ToonBridgeCelBuilder:
    """Builds interactive cel-shading and gradient LUT sampling networks."""

    @classmethod
    def build_color_ramp_expression(
        cls,
        material,
        node_data: Dict[str, Any],
        ramp_entry: Dict[str, Any],
        lut_texture_asset=None,
        is_cel_lighting_ramp: bool = False,
        incoming_driver_expr=None,
        incoming_driver_sock: str = ""
    ):
        """
        Creates a clean 1D LUT TextureSample for a ColorRamp at its exact node coordinates.
        """
        if not unreal or not material:
            return None

        loc = node_data.get("location", [0.0, 0.0])
        node_x = int(loc[0])
        node_y = int(-loc[1])  # Invert Y for Unreal layout

        # 1. Create TextureSample for the 1D LUT at (node_x, node_y)
        lut_sample = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionTextureSample, node_x, node_y
        )
        if lut_sample and lut_texture_asset:
            lut_sample.set_editor_property("texture", lut_texture_asset)
            try:
                lut_sample.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
            except Exception:
                try:
                    lut_sample.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
                except Exception:
                    pass

        # 2. Create AppendVector at (node_x - 160, node_y) for (U, 0.5) UV coordinates
        append_uv = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionAppendVector, node_x - 160, node_y
        )
        const_v = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant, node_x - 160, node_y + 100
        )
        if const_v:
            const_v.set_editor_property("r", 0.5)

        if append_uv and const_v:
            unreal.MaterialEditingLibrary.connect_material_expressions(const_v, "", append_uv, "B")
            if lut_sample:
                unreal.MaterialEditingLibrary.connect_material_expressions(append_uv, "", lut_sample, "UVs")

        # 3. Drive the U coordinate
        if is_cel_lighting_ramp:
            # Cel-Lighting path: PixelNormalWS dot Toon_SunDirection
            world_normal = unreal.MaterialEditingLibrary.create_material_expression(
                material, unreal.MaterialExpressionPixelNormalWS, node_x - 560, node_y - 60
            )

            light_vector = unreal.MaterialEditingLibrary.create_material_expression(
                material, unreal.MaterialExpressionVectorParameter, node_x - 560, node_y + 80
            )
            if light_vector:
                light_vector.set_editor_property("parameter_name", "Toon_SunDirection")
                light_vector.set_editor_property(
                    "default_value", unreal.LinearColor(0.577, 0.577, 0.577, 1.0)
                )

            dot_product = unreal.MaterialEditingLibrary.create_material_expression(
                material, unreal.MaterialExpressionDotProduct, node_x - 380, node_y
            )
            saturate = unreal.MaterialEditingLibrary.create_material_expression(
                material, unreal.MaterialExpressionSaturate, node_x - 260, node_y
            )

            if world_normal and light_vector and dot_product and saturate and append_uv:
                unreal.MaterialEditingLibrary.connect_material_expressions(world_normal, "", dot_product, "A")
                unreal.MaterialEditingLibrary.connect_material_expressions(light_vector, "", dot_product, "B")
                unreal.MaterialEditingLibrary.connect_material_expressions(dot_product, "", saturate, "")
                unreal.MaterialEditingLibrary.connect_material_expressions(saturate, "", append_uv, "A")

        elif incoming_driver_expr:
            # Driven by upstream node (e.g. UV, Separate XYZ, Noise)
            # Default to 'R' (or specific channel) to guarantee a scalar float into AppendVector
            out_pin = "R"
            if incoming_driver_sock in ("G", "Y", "Green"):
                out_pin = "G"
            elif incoming_driver_sock in ("B", "Z", "Blue"):
                out_pin = "B"
            elif incoming_driver_sock in ("A", "Alpha"):
                out_pin = "A"

            if append_uv:
                unreal.MaterialEditingLibrary.connect_material_expressions(incoming_driver_expr, out_pin, append_uv, "A")

        else:
            # Fallback constant factor
            const_u = unreal.MaterialEditingLibrary.create_material_expression(
                material, unreal.MaterialExpressionConstant, node_x - 260, node_y
            )
            if const_u:
                const_u.set_editor_property("r", 0.5)
            if append_uv and const_u:
                unreal.MaterialEditingLibrary.connect_material_expressions(const_u, "", append_uv, "A")

        return lut_sample
