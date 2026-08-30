"""
Unit tests for ToonBridge manifest and package handling.
"""

import unittest
import os
import json
import zipfile
import tempfile
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from UnrealPlugin.Content.Python.toonbridge_manifest import ToonBridgePackage


class TestToonBridgeManifest(unittest.TestCase):

    def test_sample_manifest_loading(self):
        sample_path = os.path.join(
            os.path.dirname(__file__), "..", "Samples", "StylizedGrass", "grass_manifest.json"
        )
        self.assertTrue(os.path.exists(sample_path))

        with open(sample_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(manifest.get("version"), "1.0.0")
        self.assertEqual(manifest.get("material_name"), "M_Stylized_GhibliGrass")
        self.assertIn("Material Output", manifest.get("nodes", {}))
        self.assertIn("RootTip_Mix", manifest.get("nodes", {}))
        self.assertIn("Grass_Cel_Ramp", manifest.get("nodes", {}))

    def test_package_unpack(self):
        # Create a mock .toonbridge zip file
        with tempfile.NamedTemporaryFile(suffix=".toonbridge", delete=False) as tf:
            pkg_path = tf.name

        sample_manifest_path = os.path.join(
            os.path.dirname(__file__), "..", "Samples", "StylizedGrass", "grass_manifest.json"
        )

        try:
            with zipfile.ZipFile(pkg_path, "w") as zf:
                zf.write(sample_manifest_path, "manifest.json")

            pkg = ToonBridgePackage(pkg_path)
            success = pkg.unpack()
            self.assertTrue(success)
            self.assertTrue(pkg.is_valid)
            self.assertEqual(pkg.material_name, "M_Stylized_GhibliGrass")
            self.assertEqual(len(pkg.connections), 6)
            pkg.cleanup()
        finally:
            if os.path.exists(pkg_path):
                os.remove(pkg_path)


if __name__ == "__main__":
    unittest.main()
