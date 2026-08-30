"""
ToonBridge Manifest Parser (Unreal Side)
Extracts and validates the .toonbridge package and provides structured manifest access.
"""

import os
import json
import zipfile
import tempfile
import shutil
from typing import Dict, Any, Optional, List


class ToonBridgePackage:
    """Manages an extracted .toonbridge package."""

    def __init__(self, package_path: str):
        self.package_path = package_path
        self.temp_dir = tempfile.mkdtemp(prefix="tb_ue_import_")
        self.manifest: Dict[str, Any] = {}
        self.is_valid = False

    def unpack(self) -> bool:
        """Extracts the .toonbridge ZIP archive into the temporary workspace."""
        if not os.path.exists(self.package_path):
            print(f"[ToonBridge] Package file not found: {self.package_path}")
            return False

        try:
            with zipfile.ZipFile(self.package_path, 'r') as zf:
                zf.extractall(self.temp_dir)

            manifest_path = os.path.join(self.temp_dir, "manifest.json")
            if not os.path.exists(manifest_path):
                print(f"[ToonBridge] Missing manifest.json in package.")
                return False

            with open(manifest_path, 'r', encoding='utf-8') as f:
                self.manifest = json.load(f)

            self.is_valid = True
            return True

        except Exception as e:
            print(f"[ToonBridge] Failed to unpack {self.package_path}: {e}")
            return False

    @property
    def material_name(self) -> str:
        return self.manifest.get("material_name", "M_ToonBridge_Imported")

    @property
    def nodes(self) -> Dict[str, Any]:
        return self.manifest.get("nodes", {})

    @property
    def connections(self) -> List[Dict[str, Any]]:
        return self.manifest.get("connections", [])

    @property
    def color_ramps(self) -> List[Dict[str, Any]]:
        return self.manifest.get("color_ramps", [])

    @property
    def baked_textures(self) -> List[Dict[str, Any]]:
        return self.manifest.get("baked_textures", [])

    @property
    def lut_textures(self) -> List[Dict[str, Any]]:
        return self.manifest.get("lut_textures", [])

    @property
    def outline_settings(self) -> Dict[str, Any]:
        return self.manifest.get("outline_settings", {})

    @property
    def mesh_info(self) -> Optional[Dict[str, Any]]:
        return self.manifest.get("mesh")

    def get_absolute_file_path(self, relative_path: str) -> str:
        return os.path.join(self.temp_dir, relative_path)

    def cleanup(self):
        """Removes the temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
