"""
ToonBridge Cel-Shading Builder (Unreal Engine 5)
Constructs the real-time stylized lighting sub-graph inside Unreal Materials.
"""

from typing import Dict, Any, List, Optional

try:
    import unreal
except ImportError:
    unreal = None


class ToonBridgeCelBuilder:
    """Builds interactive cel-shading networks reacting to Unreal Directional Lights."""

    @classmethod
    def build_cel_shading_network(
        cls,
        material,
        ramp_entry: Dict[str, Any],
        lut_texture_asset=None,
        base_x: int = -800,
        base_y: int = 0
    ):
        """
        Creates the N dot L lighting calculation and passes it through the ColorRamp LUT or Step math.
        Returns the final shaded color expression.
        """
        if not unreal or not material:
            return None

        # 1. World Normal Expression
        world_normal = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionPixelNormalWS, base_x, base_y
        )

        # 2. Light Vector (Vector Parameter for directional sun sync)
        light_vector = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionVectorParameter, base_x, base_y + 160
        )
        if light_vector:
            light_vector.set_editor_property("parameter_name", "Toon_SunDirection")
            # Default pointing slightly down and forward (0.577, 0.577, -0.577)
            light_vector.set_editor_property(
                "default_value", unreal.LinearColor(0.577, 0.577, 0.577, 1.0)
            )

        # 3. Dot Product (N dot L)
        dot_product = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionDotProduct, base_x + 200, base_y + 80
        )
        unreal.MaterialEditingLibrary.connect_material_expressions(
            world_normal, "", dot_product, "A"
        )
        unreal.MaterialEditingLibrary.connect_material_expressions(
            light_vector, "", dot_product, "B"
        )

        # 4. Saturate / Constant Clamp into [0.0, 1.0]
        saturate = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionSaturate, base_x + 360, base_y + 80
        )
        unreal.MaterialEditingLibrary.connect_material_expressions(
            dot_product, "", saturate, ""
        )

        # 5. Route through 1D LUT Texture or Step Math
        if lut_texture_asset:
            # 1D LUT Sampling Path
            # Append 0 to make a 2D UV coordinate (t, 0.5)
            const_v = unreal.MaterialEditingLibrary.create_material_expression(
                material, unreal.MaterialExpressionConstant, base_x + 360, base_y + 220
            )
            if const_v:
                const_v.set_editor_property("r", 0.5)

            append_uv = unreal.MaterialEditingLibrary.create_material_expression(
                material, unreal.MaterialExpressionAppendVector, base_x + 500, base_y + 120
            )
            unreal.MaterialEditingLibrary.connect_material_expressions(saturate, "", append_uv, "A")
            unreal.MaterialEditingLibrary.connect_material_expressions(const_v, "", append_uv, "B")

            lut_sample = unreal.MaterialEditingLibrary.create_material_expression(
                material, unreal.MaterialExpressionTextureSample, base_x + 680, base_y + 120
            )
            if lut_sample:
                lut_sample.set_editor_property("texture", lut_texture_asset)
                lut_sample.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
                unreal.MaterialEditingLibrary.connect_material_expressions(append_uv, "", lut_sample, "UVs")

            return lut_sample

        else:
            # Step Math Fallback Path
            # Cascaded Smoothstep / Lerp based on extracted threshold stops
            steps = ramp_entry.get("cel_steps", [])
            if not steps:
                return saturate

            last_result = None
            for idx, step in enumerate(steps):
                thresh_val = step.get("threshold", 0.5)
                col = step.get("color_rgba", [1.0, 1.0, 1.0, 1.0])

                step_col = unreal.MaterialEditingLibrary.create_material_expression(
                    material, unreal.MaterialExpressionVectorParameter, base_x + 520, base_y + (idx * 160)
                )
                if step_col:
                    step_col.set_editor_property("parameter_name", f"Toon_StepColor_{idx}")
                    step_col.set_editor_property(
                        "default_value", unreal.LinearColor(col[0], col[1], col[2], col[3] if len(col) > 3 else 1.0)
                    )

                thresh_param = unreal.MaterialEditingLibrary.create_material_expression(
                    material, unreal.MaterialExpressionScalarParameter, base_x + 520, base_y + (idx * 160) + 80
                )
                if thresh_param:
                    thresh_param.set_editor_property("parameter_name", f"Toon_Threshold_{idx}")
                    thresh_param.set_editor_property("default_value", thresh_val)

                if last_result is None:
                    last_result = step_col
                else:
                    # Lerp with step mask
                    lerp_expr = unreal.MaterialEditingLibrary.create_material_expression(
                        material, unreal.MaterialExpressionLinearInterpolate, base_x + 720, base_y + (idx * 160)
                    )
                    unreal.MaterialEditingLibrary.connect_material_expressions(last_result, "", lerp_expr, "A")
                    unreal.MaterialEditingLibrary.connect_material_expressions(step_col, "", lerp_expr, "B")
                    unreal.MaterialEditingLibrary.connect_material_expressions(saturate, "", lerp_expr, "Alpha")
                    last_result = lerp_expr

            return last_result
