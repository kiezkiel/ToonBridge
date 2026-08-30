"""
ToonBridge Unreal Plugin Initialization
Registers Editor Menu entries and initializes the Python Bridge.
"""

import unreal


def register_toonbridge_menus():
    """Adds ToonBridge tools to the Unreal Editor Toolbar."""
    try:
        menus = unreal.ToolMenus.get()
        main_menu = menus.find_menu("LevelEditor.MainMenu")
        if not main_menu:
            return

        # Add ToonBridge Menu Entry
        toonbridge_menu = main_menu.add_sub_menu(
            "LevelEditor.MainMenu",
            "ToonBridge",
            "ToonBridge",
            "ToonBridge Stylized Pipeline"
        )

        entry = unreal.ToolMenuEntry(
            name="ToonBridge.ImportPackage",
            type=unreal.MultiBoxType.MENU_ENTRY
        )
        entry.set_label("Import .toonbridge Package")
        entry.set_tool_tip("Import and reconstruct Blender stylized shader in Unreal Engine 5")
        entry.set_string_command(
            unreal.ToolMenuStringCommandType.PYTHON,
            "",
            string="import toonbridge_gui; toonbridge_gui.open_import_dialog()"
        )

        toonbridge_menu.add_menu_entry("ToonBridgeOps", entry)
        menus.refresh_all_widgets()
        unreal.log("[ToonBridge] Successfully registered Unreal Editor menus.")

    except Exception as e:
        unreal.log_warning(f"[ToonBridge] Failed to register menus: {e}")


if __name__ == "__main__":
    register_toonbridge_menus()
