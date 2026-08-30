"""
ToonBridge Sidebar UI Panels for Blender Shader Editor & 3D View.
"""

try:
    import bpy
    from bpy.types import Panel
except ImportError:
    bpy = None
    Panel = object


class NODE_PT_ToonBridgePanel(Panel):
    """Main ToonBridge export panel in the Shader Editor sidebar."""
    bl_label = "ToonBridge Exporter"
    bl_idname = "NODE_PT_toonbridge_main"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "ToonBridge"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.toonbridge_settings

        # Active Selection Info
        obj = context.active_object
        box = layout.box()
        box.label(text="Active Selection:", icon='OBJECT_DATA')
        if obj and obj.type == 'MESH':
            box.label(text=f"Mesh: {obj.name}", icon='MESH_DATA')
            if obj.active_material:
                box.label(text=f"Material: {obj.active_material.name}", icon='MATERIAL')
            else:
                box.label(text="No active material!", icon='ERROR')
        else:
            box.label(text="Select a Mesh Object", icon='INFO')

        # Export Package Settings
        col = layout.column(align=True)
        col.prop(settings, "package_name")
        col.prop(settings, "export_path")
        col.prop(settings, "export_mesh")

        # Export Button
        layout.separator()
        row = layout.row()
        row.scale_y = 1.8
        row.operator("toonbridge.export", text="Export to Unreal (.toonbridge)", icon='EXPORT')


class NODE_PT_ToonBridgeCelSettings(Panel):
    """Cel-shading and ColorRamp conversion settings."""
    bl_label = "Cel-Shading & Lighting"
    bl_idname = "NODE_PT_toonbridge_cel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "ToonBridge"
    bl_parent_id = "NODE_PT_toonbridge_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        settings = context.scene.toonbridge_settings

        col = layout.column(align=True)
        col.prop(settings, "cel_mode")

        layout.separator()
        col = layout.column(align=True)
        col.prop(settings, "auto_outline")
        if settings.auto_outline:
            col.prop(settings, "outline_width")


class NODE_PT_ToonBridgeBakeSettings(Panel):
    """Procedural Noise Bake Settings."""
    bl_label = "Procedural Texture Baking"
    bl_idname = "NODE_PT_toonbridge_bake"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "ToonBridge"
    bl_parent_id = "NODE_PT_toonbridge_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        settings = context.scene.toonbridge_settings

        col = layout.column(align=True)
        col.prop(settings, "bake_resolution")
        col.label(text="Auto-bakes Voronoi/Noise to seamless PNGs", icon='INFO')
