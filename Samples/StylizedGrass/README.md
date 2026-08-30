# Stylized Grass Sample

This sample contains an example serialized **Stylized Grass Material** (`grass_manifest.json`) demonstrating how ToonBridge converts:
1. **Root-to-Tip Gradient:** `TextureCoordinate` $\rightarrow$ `SeparateXYZ (Y channel)` $\rightarrow$ `MixRGB` (dark ambient root to sunny tip).
2. **Cel Shadowing:** `ShaderToRGB` $\rightarrow$ `ColorRamp` with a 2-stop anime shadow threshold (0.45 cutoff with cool blue-tinted shadows).
3. **Lighting Synthesis:** Multiplies the gradient base color with the directional cel-shadow factor.
