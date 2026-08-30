"""
ToonBridge GUI & Native Windows Dialog Prompts (Unreal Engine 5)
Uses native Windows Forms file picker (no Tkinter required, zero dependency on embedded Python modules).
"""

import os
import sys
import subprocess
from typing import Optional

try:
    import unreal
except ImportError:
    unreal = None

# Ensure current directory is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from toonbridge_importer import ToonBridgeImporter


def get_file_path_native() -> str:
    """Invokes a native Windows File Dialog without needing Tkinter or external Python GUI libraries."""
    ps_cmd = (
        "[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; "
        "$f = New-Object System.Windows.Forms.OpenFileDialog; "
        "$f.Filter = 'ToonBridge Package (*.toonbridge)|*.toonbridge|All Files (*.*)|*.*'; "
        "$f.Title = 'Select ToonBridge Package (.toonbridge)'; "
        "$f.TopMost = $true; "
        "if ($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { Write-Host $f.FileName }"
    )
    try:
        CREATE_NO_WINDOW = 0x08000000
        result = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            text=True,
            creationflags=CREATE_NO_WINDOW
        ).strip()
        return result
    except Exception as e:
        if unreal:
            unreal.log_warning(f"[ToonBridge] File dialog exception: {e}")
        return ""


def open_import_dialog():
    """Main entry point for importing a .toonbridge package."""
    if unreal:
        unreal.log("[ToonBridge] Opening native file picker...")

    file_path = get_file_path_native()

    if not file_path:
        if unreal:
            unreal.log("[ToonBridge] Import cancelled (no file selected).")
        return

    if unreal:
        unreal.log(f"[ToonBridge] Selected package: {file_path}")
        importer = ToonBridgeImporter()
        success = importer.import_package(file_path)

        if success:
            unreal.EditorDialog.show_message(
                "ToonBridge Import Complete",
                f"Successfully imported and reconstructed:\n\n{file_path}\n\nAssets saved in /Game/ToonBridge/",
                unreal.AppMsgType.OK
            )
        else:
            unreal.EditorDialog.show_message(
                "ToonBridge Import Failed",
                f"Failed to import:\n\n{file_path}\n\nPlease check the Output Log for details.",
                unreal.AppMsgType.OK
            )


if __name__ == "__main__":
    open_import_dialog()
