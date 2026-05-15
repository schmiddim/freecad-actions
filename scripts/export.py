"""Export FreeCAD .FCStd files to STL and STEP formats.

Reads configuration from gallery.yaml to determine which directory
to search for .FCStd files (non-recursive).
"""

import FreeCAD, Mesh, Part
import os
import glob

try:
    import yaml
except ImportError:
    # Fallback: parse simple key: "value" lines from gallery.yaml
    yaml = None


def load_config():
    """Load gallery.yaml configuration."""
    config_path = os.path.join(os.getcwd(), "gallery.yaml")
    defaults = {
        "freecad_dir": ".",
        "exports_dir": "exports",
    }

    if not os.path.exists(config_path):
        print("Warning: gallery.yaml not found, using defaults")
        return defaults

    if yaml:
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        return {**defaults, **(cfg or {})}

    # Simple fallback parser for environments without PyYAML
    config = dict(defaults)
    with open(config_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key in defaults:
                    config[key] = val
    return config


def main():
    config = load_config()
    freecad_dir = config["freecad_dir"]
    exports_dir = config["exports_dir"]

    os.makedirs(exports_dir, exist_ok=True)

    # Non-recursive: only *.FCStd directly in freecad_dir
    pattern = os.path.join(freecad_dir, "*.FCStd")
    fcstd_files = glob.glob(pattern)

    if not fcstd_files:
        print(f"No .FCStd files found in '{freecad_dir}'")
        return

    print(f"Found {len(fcstd_files)} .FCStd files in '{freecad_dir}'")

    for fcstd in fcstd_files:
        doc = FreeCAD.openDocument(fcstd)
        name = os.path.splitext(os.path.basename(fcstd))[0]

        exported = False
        for obj in doc.Objects:
            if obj.isDerivedFrom("Part::Feature") and not obj.Shape.isNull():
                stl_path = os.path.join(exports_dir, f"{name}.stl")
                step_path = os.path.join(exports_dir, f"{name}.step")
                Mesh.export([obj], stl_path)
                Part.export([obj], step_path)
                print(f"  Exported: {name}.stl + {name}.step")
                exported = True
                break  # first valid object

        if not exported:
            print(f"  Warning: No valid Part::Feature found in {fcstd}")

        FreeCAD.closeDocument(doc.Name)

    print(f"Export complete: {len(fcstd_files)} models -> {exports_dir}/")


main()
