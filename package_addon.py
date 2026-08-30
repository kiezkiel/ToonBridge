#!/usr/bin/env python3
"""
ToonBridge Addon Packaging Utility
Zips the BlenderAddon directory into a clean, installable ToonBridge-Blender.zip archive.
"""

import os
import zipfile
import shutil

def package_addon():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.join(root_dir, "BlenderAddon")
    output_dir = os.path.join(root_dir, "dist")
    os.makedirs(output_dir, exist_ok=True)
    
    zip_path = os.path.join(output_dir, "ToonBridge-Blender.zip")
    
    print(f"[ToonBridge] Packaging Blender Add-on from: {source_dir}")
    print(f"[ToonBridge] Output target: {zip_path}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            # Ignore __pycache__ and test files
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for file in files:
                if file.endswith(('.pyc', '.pyo', '.pyd', '.git', '.DS_Store')):
                    continue
                abs_path = os.path.join(root, file)
                rel_path = os.path.join("ToonBridge", os.path.relpath(abs_path, source_dir))
                zf.write(abs_path, rel_path)
                
    print(f"[ToonBridge] Successfully created: {zip_path} ({os.path.getsize(zip_path)} bytes)")

if __name__ == "__main__":
    package_addon()
