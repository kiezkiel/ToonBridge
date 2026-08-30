"""
ToonBridge Blender Add-on
1-Click Blender EEVEE to Unreal Engine 5 Stylized Shader Bridge
"""

bl_info = {
    "name": "ToonBridge",
    "author": "ToonBridge Team",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "Shader Editor > Sidebar > ToonBridge",
    "description": "Bridges Blender EEVEE Stylized / Cel Shaders into Unreal Engine 5",
    "warning": "",
    "doc_url": "https://github.com/kiezkiel/ToonBridge",
    "tracker_url": "https://github.com/kiezkiel/ToonBridge/issues",
    "category": "Pipeline",
}

try:
    import bpy
    from bpy.props import (
        StringProperty,
        BoolProperty,
        EnumProperty,
        IntProperty,
        FloatProperty,
        PointerProperty,
    )
    from bpy.types import PropertyGroup, Operator
except ImportError:
    bpy = None
    PropertyGroup = object
    Operator = object
    StringProperty = BoolProperty = EnumProperty = IntProperty = FloatProperty = PointerProperty = lambda **kwargs: None

from .core.exporter import ToonBridgeExporter
from .ui.panels import (
    NODE_PT_ToonBridgePanel,
    NODE_PT_ToonBridgeBakeSettings,
    NODE_PT_ToonBridgeCelSettings,
)


class ToonBridgeSettings(PropertyGroup):
    export_path: StringProperty(
        name="Export Directory",
        description="Directory to save the .toonbridge package",
        default="//",
        subtype='DIR_PATH',
    )
    package_name: StringProperty(
        name="Package Name",
        description="Name of the exported .toonbridge file",
        default="StylizedAsset",
    )
    cel_mode: EnumProperty(
        name="Cel Shading Mode",
        description="How to translate ColorRamp and lighting steps into Unreal Engine",
        items=[
            ('HYBRID', "Hybrid (Auto-Detect)", "Use Step Math for <=4 stops, 1D LUT for smooth ramps"),
            ('STEP_MATH', "Crisp Step Math", "Reconstruct via smoothstep & step math expressions in UE"),
            ('LUT_TEXTURE', "1D Gradient LUT", "Bake 256x1 LUT texture for exact color ramp matching"),
        ],
        default='HYBRID',
    )
    bake_resolution: EnumProperty(
        name="Bake Resolution",
        description="Resolution for baked procedural noise textures",
        items=[
            ('1024', "1024 x 1024 (1K)", "Fast bake, low memory"),
            ('2048', "2048 x 2048 (2K)", "Balanced quality and performance"),
            ('4048', "4096 x 4096 (4K)", "Ultra high definition"),
        ],
        default='2048',
    )
    export_mesh: BoolProperty(
        name="Export Mesh (FBX)",
        description="Export the active object mesh with custom split normals alongside material",
        default=True,
    )
    auto_outline: BoolProperty(
        name="Export Inverted Hull Outline",
        description="Detect and export Solidify outline settings for Unreal vertex offset",
        default=True,
    )
    outline_width: FloatProperty(
        name="Outline Thickness",
        description="Default outline thickness multiplier",
        default=0.02,
        min=0.0,
        max=1.0,
    )


class TOONBRIDGE_OT_Export(Operator):
    """Export the active stylized material and mesh to a .toonbridge package"""
    bl_idname = "toonbridge.export"
    bl_label = "Export ToonBridge Package"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a valid Mesh object.")
            return {'CANCELLED'}

        mat = obj.active_material
        if not mat or not mat.use_nodes or not mat.node_tree:
            self.report({'ERROR'}, "Active object has no node-based material.")
            return {'CANCELLED'}

        settings = context.scene.toonbridge_settings
        exporter = ToonBridgeExporter(context, settings)
        success, message = exporter.export_package(obj, mat)

        if success:
            self.report({'INFO'}, f"ToonBridge: {message}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"ToonBridge Export Failed: {message}")
            return {'CANCELLED'}


classes = (
    ToonBridgeSettings,
    TOONBRIDGE_OT_Export,
    NODE_PT_ToonBridgePanel,
    NODE_PT_ToonBridgeBakeSettings,
    NODE_PT_ToonBridgeCelSettings,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.toonbridge_settings = PointerProperty(type=ToonBridgeSettings)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.toonbridge_settings


if __name__ == "__main__":
    register()
