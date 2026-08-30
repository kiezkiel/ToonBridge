"""
ToonBridge Unreal Plugin Initialization
Registers Editor Menu entries and Toolbar buttons across all UE5 versions (5.0 - 5.8+).
"""

import os
import sys
import unreal

# Ensure plugin Python directory is in sys.path
plugin_python_dir = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
if plugin_python_dir not in sys.path:
    sys.path.insert(0, plugin_python_dir)


def register_toonbridge_menus():
    """Adds ToonBridge tools to the Unreal Editor Menus & Toolbar."""
    try:
        menus = unreal.ToolMenus.get()

        command_str = (
            f"import sys, os; "
            f"p = r'{plugin_python_dir}'; "
            f"sys.path.insert(0, p) if p not in sys.path else None; "
            f"import toonbridge_gui; toonbridge_gui.open_import_dialog()"
        )

        # 1. Add to the standard "Tools" Menu
        tools_menu = menus.find_menu("LevelEditor.MainMenu.Tools")
        if tools_menu:
            entry = unreal.ToolMenuEntry(name="ToonBridge.ToolsImport")
            entry.set_label("ToonBridge: Import .toonbridge Package")
            entry.set_tool_tip("Import and reconstruct Blender stylized shader in Unreal Engine 5")
            entry.set_string_command(
                unreal.ToolMenuStringCommandType.PYTHON,
                "",
                string=command_str
            )
            tools_menu.add_menu_entry("Scripting", entry)

        # 2. Add Top-Level ToonBridge Menu
        main_menu = menus.find_menu("LevelEditor.MainMenu")
        if main_menu:
            sub_menu = main_menu.add_sub_menu(
                main_menu.get_name(),
                "ToonBridgeSection",
                "ToonBridgeMenu",
                "ToonBridge"
            )
            if sub_menu:
                sub_entry = unreal.ToolMenuEntry(name="ToonBridge.MainMenuImport")
                sub_entry.set_label("Import .toonbridge Package")
                sub_entry.set_tool_tip("Import and reconstruct Blender stylized shader in Unreal Engine 5")
                sub_entry.set_string_command(
                    unreal.ToolMenuStringCommandType.PYTHON,
                    "",
                    string=command_str
                )
                sub_menu.add_menu_entry("Imports", sub_entry)

        # 3. Add to Main Editor Toolbar
        toolbar = menus.find_menu("LevelEditor.LevelEditorToolBar.User")
        if not toolbar:
            toolbar = menus.find_menu("LevelEditor.LevelEditorToolBar")

        if toolbar:
            tb_entry = unreal.ToolMenuEntry(name="ToonBridge.ToolbarImport")
            tb_entry.set_label("ToonBridge Import")
            tb_entry.set_tool_tip("Import Blender .toonbridge Package")
            tb_entry.set_string_command(
                unreal.ToolMenuStringCommandType.PYTHON,
                "",
                string=command_str
            )
            toolbar.add_menu_entry("ToonBridgeBar", tb_entry)

        menus.refresh_all_widgets()
        unreal.log("[ToonBridge] Registered ToonBridge tools in Tools menu, Top menu, and Toolbar.")

    except Exception as e:
        unreal.log_warning(f"[ToonBridge] Failed to register menus: {e}")


if __name__ == "__main__":
    register_toonbridge_menus()
