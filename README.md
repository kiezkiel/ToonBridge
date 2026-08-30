# ToonBridge 🎨
> **The 1-Click Blender EEVEE to Unreal Engine 5 Stylized Shader Bridge**

[![Blender 3.6+](https://img.shields.io/badge/Blender-3.6%20%7C%204.0%20%7C%204.1%20%7C%204.2-orange.svg)](https://www.blender.org/)
[![Unreal Engine 5.1+](https://img.shields.io/badge/Unreal%20Engine-5.1%20%7C%205.2%20%7C%205.3%20%7C%205.4%20%7C%205.5-blue.svg)](https://www.unrealengine.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🌟 The Problem ToonBridge Solves

When creating stylized art (anime, cel-shaded, Ghibli, comic) in Blender's EEVEE engine, artists rely heavily on:
* **`Shader to RGB`** (evaluates realtime lighting inside the material)
* **`ColorRamp`** (stepped thresholds, anime shadow tints, custom gradients)
* **Procedural Noises** (Voronoi, Musgrave, Wave textures)

Exporting these materials to Unreal Engine 5 using standard FBX or glTF breaks completely because **Unreal Engine uses a Deferred Shading pipeline** where materials cannot evaluate lights directly.

**ToonBridge bridges this architectural gap:**
1. **Graph Serialization:** Automatically parses Blender's mathematical shader trees into a clean Intermediate Representation (IR).
2. **ColorRamp & Cel-Shading Translation:** Converts `Shader to RGB` and `ColorRamp` stops into Unreal-compatible Cel-Shading Material Functions and 1D Gradient LUTs.
3. **Automated Procedural Baking:** Isolates non-transferable procedural noises (Voronoi, Musgrave) and auto-bakes them into game-ready textures.
4. **1-Click Container Packaging:** Bundles the mesh, textures, LUTs, and graph manifest into a single `.toonbridge` container.
5. **Native Unreal Reconstruction:** Rebuilds the material graph inside Unreal Engine using `unreal.MaterialEditingLibrary`.

---

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                      BLENDER EEVEE                       │
│  - Shader Editor N-Panel (ToonBridge)                    │
│  - Graph Parser (Math, Mix, Vector, MapRange)            │
│  - ColorRamp Extractor (Step Math / 256x1 1D LUT)        │
│  - Noise Baker (Automated Cycles/EEVEE background bake)  │
│  - Exporter -> Generates .toonbridge package             │
└────────────────────────────┬─────────────────────────────┘
                             │
                     [.toonbridge bundle]
                             │
┌────────────────────────────▼─────────────────────────────┐
│                  UNREAL ENGINE 5 PLUGIN                  │
│  - Editor Toolbar / Utility Widget ("Import ToonBridge") │
│  - Manifest Parser & Asset Importer (FBX + Textures)     │
│  - Cel-Shading Builder (MPC_ToonLighting / Light Vector) │
│  - Node Factory (Instantiates & connects UExpressions)   │
│  - Final Cel-Shaded Material / Material Instance         │
└──────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start Guide

### 1. Blender Add-on Installation
1. Run `python package_addon.py` or download `ToonBridge-Blender.zip`.
2. In Blender: **Edit** $\rightarrow$ **Preferences** $\rightarrow$ **Add-ons** $\rightarrow$ **Install...** $\rightarrow$ Select `ToonBridge-Blender.zip`.
3. Enable the **"Pipeline: ToonBridge"** checkbox.
4. In the **Shader Editor**, press `N` to open the sidebar and navigate to the **ToonBridge** tab.

### 2. Unreal Engine 5 Plugin Installation
1. Copy the `UnrealPlugin/` folder into your Unreal Engine project's `Plugins/ToonBridge` directory.
2. Enable **Python Editor Script Plugin** and **Editor Scripting Utilities** in Unreal (Edit $\rightarrow$ Plugins).
3. Restart Unreal Engine.
4. Click the **ToonBridge** button on the editor toolbar or run the importer from the Content Browser.

### 3. The 1-Click Workflow
1. **In Blender:** Select your stylized mesh/material $\rightarrow$ In the ToonBridge panel, choose your settings (Cel Mode, Resolution) $\rightarrow$ Click **"Export ToonBridge Package (.toonbridge)"**.
2. **In Unreal Engine 5:** Click **"Import ToonBridge Package"** $\rightarrow$ Select the `.toonbridge` file.
3. **Done!** Your mesh and material are imported, compiled, and ready with interactive cel-shading reacting to your Unreal Directional Light.

---

## 📦 Repository Structure

```
ToonBridge/
├── BlenderAddon/              # Blender Add-on source code
│   ├── __init__.py            # Addon registration & bl_info
│   ├── core/                  # Graph walker, LUT generator, baker, exporter
│   └── ui/                    # Shader editor N-panel
├── UnrealPlugin/              # Unreal Engine 5 Plugin
│   ├── ToonBridge.uplugin     # Plugin descriptor
│   └── Content/Python/        # Python automation bridge & material node builder
├── Samples/                   # Verification samples (Stylized Grass)
├── tests/                     # Unit tests for graph parsing and LUT generation
├── package_addon.py           # Add-on packaging script
└── README.md
```

---

## 📄 License
Released under the [MIT License](LICENSE).
