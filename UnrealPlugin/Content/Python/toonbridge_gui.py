"""
ToonBridge GUI & Native Windows Dialog Prompts (Unreal Engine 5)
Uses pure Windows ctypes comdlg32 (zero external dependencies, runs natively inside Unreal's embedded Python).
"""

import os
import sys
import ctypes
from ctypes import wintypes
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


class OPENFILENAME(ctypes.Structure):
    _fields_ = [
        ('lStructSize', wintypes.DWORD),
        ('hwndOwner', wintypes.HWND),
        ('hInstance', wintypes.HINSTANCE),
        ('lpstrFilter', wintypes.LPCWSTR),
        ('lpstrCustomFilter', wintypes.LPWSTR),
        ('nMaxCustFilter', wintypes.DWORD),
        ('nFilterIndex', wintypes.DWORD),
        ('lpstrFile', wintypes.LPWSTR),
        ('nMaxFile', wintypes.DWORD),
        ('lpstrFileTitle', wintypes.LPWSTR),
        ('nMaxFileTitle', wintypes.DWORD),
        ('lpstrInitialDir', wintypes.LPCWSTR),
        ('lpstrTitle', wintypes.LPCWSTR),
        ('Flags', wintypes.DWORD),
        ('nFileOffset', wintypes.WORD),
        ('nFileExtension', wintypes.WORD),
        ('lpstrDefExt', wintypes.LPCWSTR),
        ('lCustData', wintypes.LPARAM),
        ('lpfnHook', wintypes.LPVOID),
        ('lpTemplateName', wintypes.LPCWSTR),
        ('pvReserved', wintypes.LPVOID),
        ('dwReserved', wintypes.DWORD),
        ('FlagsEx', wintypes.DWORD),
    ]


def get_file_path_native() -> str:
    """Opens a native Windows OpenFileName dialog via comdlg32."""
    OFN_EXPLORER = 0x00080000
    OFN_FILEMUSTEXIST = 0x00001000
    OFN_PATHMUSTEXIST = 0x00000800
    OFN_NOCHANGEDIR = 0x00000008

    filter_str = "ToonBridge Package (*.toonbridge)\0*.toonbridge\0All Files (*.*)\0*.*\0\0"
    buffer = ctypes.create_unicode_buffer(1024)

    ofn = OPENFILENAME()
    ofn.lStructSize = ctypes.sizeof(OPENFILENAME)
    ofn.hwndOwner = None
    ofn.lpstrFilter = filter_str
    ofn.lpstrFile = ctypes.cast(buffer, wintypes.LPWSTR)
    ofn.nMaxFile = 1024
    ofn.lpstrTitle = "Select ToonBridge Package (.toonbridge)"
    ofn.Flags = OFN_EXPLORER | OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST | OFN_NOCHANGEDIR

    if ctypes.windll.comdlg32.GetOpenFileNameW(ctypes.byref(ofn)):
        return buffer.value
    return ""


def open_import_dialog():
    """Main entry point for importing a .toonbridge package."""
    if unreal:
        unreal.log("[ToonBridge] Opening native file picker dialog...")

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
