"""
ToonBridge ColorRamp Parser & 1D Gradient LUT Generator
Translates Blender ColorRamp stops into either smoothstep math parameters or 256x1 1D LUT PNG textures.
"""

import math
import struct
import zlib
from typing import List, Dict, Any, Tuple, Optional


class ColorRampParser:
    """Parses Blender ColorRamp node data and generates 1D Gradient LUT textures."""

    @staticmethod
    def evaluate_ramp_at_t(stops: List[Dict[str, Any]], t: float, interpolation: str = 'LINEAR') -> Tuple[float, float, float, float]:
        """Evaluates interpolated RGBA at position t in [0.0, 1.0] given a list of ramp stops."""
        if not stops:
            return (1.0, 1.0, 1.0, 1.0)

        # Clamp t
        t = max(0.0, min(1.0, float(t)))

        # Sorted stops by position
        sorted_stops = sorted(stops, key=lambda s: s["position"])

        if t <= sorted_stops[0]["position"]:
            c = sorted_stops[0]["color"]
            return (c[0], c[1], c[2], c[3] if len(c) > 3 else 1.0)

        if t >= sorted_stops[-1]["position"]:
            c = sorted_stops[-1]["color"]
            return (c[0], c[1], c[2], c[3] if len(c) > 3 else 1.0)

        # Find enclosing pair
        for i in range(len(sorted_stops) - 1):
            s0 = sorted_stops[i]
            s1 = sorted_stops[i + 1]
            p0, p1 = s0["position"], s1["position"]
            if p0 <= t <= p1:
                c0 = s0["color"]
                c1 = s1["color"]
                if p1 == p0:
                    factor = 0.0
                else:
                    factor = (t - p0) / (p1 - p0)

                if interpolation == 'CONSTANT':
                    return (c0[0], c0[1], c0[2], c0[3] if len(c0) > 3 else 1.0)

                elif interpolation in ('EASE', 'CARDINAL', 'B_SPLINE'):
                    # Smooth hermite interpolation factor
                    factor = factor * factor * (3.0 - 2.0 * factor)

                # Linear interpolation
                r = c0[0] + (c1[0] - c0[0]) * factor
                g = c0[1] + (c1[1] - c0[1]) * factor
                b = c0[2] + (c1[2] - c0[2]) * factor
                a0 = c0[3] if len(c0) > 3 else 1.0
                a1 = c1[3] if len(c1) > 3 else 1.0
                a = a0 + (a1 - a0) * factor
                return (r, g, b, a)

        c = sorted_stops[-1]["color"]
        return (c[0], c[1], c[2], c[3] if len(c) > 3 else 1.0)

    @classmethod
    def generate_lut_buffer(cls, ramp_data: Dict[str, Any], width: int = 256) -> bytes:
        """Generates raw RGBA byte buffer (width x 1) for the color ramp."""
        stops = ramp_data.get("stops", [])
        interpolation = ramp_data.get("interpolation", "LINEAR")
        raw_bytes = bytearray()

        for x in range(width):
            t = x / float(width - 1) if width > 1 else 0.0
            r, g, b, a = cls.evaluate_ramp_at_t(stops, t, interpolation)
            ir = max(0, min(255, int(r * 255.0 + 0.5)))
            ig = max(0, min(255, int(g * 255.0 + 0.5)))
            ib = max(0, min(255, int(b * 255.0 + 0.5)))
            ia = max(0, min(255, int(a * 255.0 + 0.5)))
            raw_bytes.extend([ir, ig, ib, ia])

        return bytes(raw_bytes)

    @classmethod
    def save_lut_png(cls, ramp_data: Dict[str, Any], filepath: str, width: int = 256) -> bool:
        """Saves a standalone uncompressed 1D PNG (width x 1) without external dependencies."""
        raw_rgba = cls.generate_lut_buffer(ramp_data, width=width)
        height = 1

        # Build raw PNG format
        def make_chunk(chunk_type: bytes, data: bytes) -> bytes:
            length = struct.pack(">I", len(data))
            crc = struct.pack(">I", zlib.crc32(chunk_type + data) & 0xffffffff)
            return length + chunk_type + data + crc

        png_header = b"\x89PNG\r\n\x1a\n"
        # IHDR: Width, Height, BitDepth=8, ColorType=6 (RGBA), Comp=0, Filter=0, Interlace=0
        ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
        ihdr_chunk = make_chunk(b"IHDR", ihdr_data)

        # IDAT: Scanlines with filter byte 0 (None)
        scanline = b"\x00" + raw_rgba
        compressed_data = zlib.compress(scanline, level=9)
        idat_chunk = make_chunk(b"IDAT", compressed_data)

        # IEND
        iend_chunk = make_chunk(b"IEND", b"")

        try:
            with open(filepath, "wb") as f:
                f.write(png_header + ihdr_chunk + idat_chunk + iend_chunk)
            return True
        except Exception as e:
            print(f"[ToonBridge] Error writing LUT PNG to {filepath}: {e}")
            return False

    @classmethod
    def extract_cel_step_parameters(cls, ramp_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extracts mathematical step points suitable for direct UE Smoothstep / Step expressions."""
        stops = sorted(ramp_data.get("stops", []), key=lambda s: s["position"])
        steps = []
        for i, stop in enumerate(stops):
            steps.append({
                "step_index": i,
                "threshold": float(stop["position"]),
                "color_rgba": [float(c) for c in stop["color"]],
            })
        return steps
