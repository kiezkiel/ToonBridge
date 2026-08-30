"""
Unit tests for ColorRampParser and 1D Gradient LUT generation.
"""

import unittest
import os
import tempfile
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from BlenderAddon.core.color_ramp_parser import ColorRampParser


class TestColorRampParser(unittest.TestCase):

    def test_evaluate_constant_ramp(self):
        stops = [
            {"position": 0.0, "color": [0.0, 0.0, 0.0, 1.0]},
            {"position": 0.5, "color": [1.0, 1.0, 1.0, 1.0]},
        ]
        # Before 0.5 should be black
        col_0 = ColorRampParser.evaluate_ramp_at_t(stops, 0.2, interpolation='CONSTANT')
        self.assertAlmostEqual(col_0[0], 0.0)
        self.assertAlmostEqual(col_0[1], 0.0)
        self.assertAlmostEqual(col_0[2], 0.0)

        # At or above 0.5 should be white
        col_1 = ColorRampParser.evaluate_ramp_at_t(stops, 0.6, interpolation='CONSTANT')
        self.assertAlmostEqual(col_1[0], 1.0)
        self.assertAlmostEqual(col_1[1], 1.0)
        self.assertAlmostEqual(col_1[2], 1.0)

    def test_evaluate_linear_ramp(self):
        stops = [
            {"position": 0.0, "color": [0.0, 0.0, 0.0, 1.0]},
            {"position": 1.0, "color": [1.0, 1.0, 1.0, 1.0]},
        ]
        col_mid = ColorRampParser.evaluate_ramp_at_t(stops, 0.5, interpolation='LINEAR')
        self.assertAlmostEqual(col_mid[0], 0.5, delta=0.01)
        self.assertAlmostEqual(col_mid[1], 0.5, delta=0.01)
        self.assertAlmostEqual(col_mid[2], 0.5, delta=0.01)

    def test_generate_lut_png(self):
        ramp_data = {
            "interpolation": "LINEAR",
            "stops": [
                {"position": 0.0, "color": [1.0, 0.0, 0.0, 1.0]},
                {"position": 1.0, "color": [0.0, 0.0, 1.0, 1.0]}
            ]
        }
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
            temp_path = tf.name

        try:
            success = ColorRampParser.save_lut_png(ramp_data, temp_path, width=256)
            self.assertTrue(success)
            self.assertTrue(os.path.exists(temp_path))
            self.assertGreater(os.path.getsize(temp_path), 50)

            # Check PNG magic bytes
            with open(temp_path, "rb") as f:
                header = f.read(8)
                self.assertEqual(header, b"\x89PNG\r\n\x1a\n")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
