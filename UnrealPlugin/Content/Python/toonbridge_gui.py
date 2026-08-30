"""
ToonBridge GUI & Dialog Prompts (Unreal Engine 5)
Provides file picker and interactive import interface inside the Unreal Editor.
"""

import tkinter as tk
from tkinter import filedialog
from typing import Optional

try:
    import unreal
except ImportError:
    unreal = None

from .toonbridge_importer import ToonBridgeImporter


def open_import_dialog():
    """Opens a native file picker dialog to select a .toonbridge package."""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    file_path = filedialog.askopenfilename(
        title="Select ToonBridge Package (.toonbridge)",
        filetypes=[("ToonBridge Package", "*.toonbridge"), ("All Files", "*.*")]
    )
    root.destroy()

    if not file_path:
        if unreal:
            unreal.log("[ToonBridge] Import cancelled by user.")
        return

    if unreal:
        unreal.log(f"[ToonBridge] Selected package: {file_path}")
        importer = ToonBridgeImporter()
        success = importer.import_package(file_path)

        if success:
            unreal.EditorDialog.show_message(
                "ToonBridge Import Complete",
                f"Successfully imported and reconstructed:\n{file_path}\n\nAssets saved in /Game/ToonBridge/",
                unreal.AppMsgType.OK
            )
        else:
            unreal.EditorDialog.show_message(
                "ToonBridge Import Failed",
                f"Failed to import:\n{file_path}\nPlease check the Output Log for details.",
                unreal.AppMsgType.OK
            )
