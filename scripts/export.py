"""Export FreeCAD .FCStd files to STL and STEP formats.

Reads configuration from cad-gallery.yaml to determine which directory
to search for .FCStd files (non-recursive).
"""

import FreeCAD, Mesh, Part
import os
import sys
import glob

# Try to import FreeCADGui for thumbnail generation
try:
    import FreeCADGui
    HAS_GUI = True
except ImportError:
    HAS_GUI = False
    safe_print = print  # Fallback for safe_print before it's defined

# Try to import trimesh for STL-based thumbnail generation
try:
    import trimesh
    import matplotlib
    matplotlib.use('Agg')  # Non-GUI backend
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    HAS_TRIMESH = True
except ImportError:
    HAS_TRIMESH = False

# Ensure UTF-8 encoding for stdout/stderr
if sys.version_info >= (3, 7):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
else:
    # Fallback for older Python versions
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')

try:
    import yaml
except ImportError:
    # Fallback: parse simple key: "value" lines from cad-gallery.yaml
    yaml = None


def safe_print(msg):
    """Print with UTF-8 error handling for environments with encoding issues."""
    try:
        print(msg)
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Fallback: print ASCII representation
        try:
            print(msg.encode('ascii', errors='replace').decode('ascii'))
        except:
            print("[UTF-8 encoding error in message]")


def load_config():
    """Load cad-gallery.yaml configuration."""
    config_path = os.path.join(os.getcwd(), "cad-gallery.yaml")
    defaults = {
        "freecad_dir": ".",
        "exports_dir": "exports",
    }

    if not os.path.exists(config_path):
        # Fallback to old name for backwards compatibility
        config_path = os.path.join(os.getcwd(), "gallery.yaml")

    if not os.path.exists(config_path):
        safe_print("Warning: cad-gallery.yaml not found, using defaults")
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


def generate_thumbnail_from_stl(stl_path, thumbnails_dir, name):
    """Generate thumbnail from STL file using trimesh."""
    if not HAS_TRIMESH:
        return False
    
    try:
        # Load STL mesh
        mesh = trimesh.load(stl_path)
        
        # Create figure with white background (800x600 pixels at 100 DPI)
        fig = plt.figure(figsize=(8, 6), dpi=100, facecolor='white')
        ax = fig.add_subplot(111, projection='3d', facecolor='white')
        
        # Plot the mesh
        vertices = mesh.vertices
        faces = mesh.faces
        
        # Create a 3D mesh plot
        ax.plot_trisurf(vertices[:, 0], vertices[:, 1], faces, vertices[:, 2],
                       color='#e94560', alpha=0.9, edgecolor='none', 
                       linewidth=0, antialiased=True, shade=True)
        
        # Set viewpoint (isometric-like)
        ax.view_init(elev=30, azim=45)
        
        # Remove axes
        ax.set_axis_off()
        
        # Auto-scale to fit
        ax.auto_scale_xyz(vertices[:, 0], vertices[:, 1], vertices[:, 2])
        
        # Set aspect ratio
        ax.set_box_aspect([1,1,1])
        
        # Save thumbnail (800x600 pixels)
        thumb_path = os.path.join(thumbnails_dir, f"{name}.png")
        fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        plt.savefig(thumb_path, dpi=100, facecolor='white', edgecolor='none')
        plt.close(fig)
        
        safe_print(f"  Thumbnail: {name}.png (800x600)")
        return True
        
    except Exception as e:
        safe_print(f"  Warning: STL thumbnail generation failed: {e}")
        return False


def generate_thumbnail(doc, obj, name, thumbnails_dir):
    """Generate a thumbnail image (800x600) for the given object."""
    # This function is called during export but we'll generate from STL after
    return False


def main():
    config = load_config()
    freecad_dir = config["freecad_dir"]
    exports_dir = config["exports_dir"]

    os.makedirs(exports_dir, exist_ok=True)
    
    # Create thumbnails directory
    thumbnails_dir = os.path.join(exports_dir, "thumbnails")
    os.makedirs(thumbnails_dir, exist_ok=True)
    
    if HAS_TRIMESH:
        safe_print("trimesh available - thumbnails will be generated from STL files")
    elif HAS_GUI:
        safe_print("FreeCADGui available but not used (prefer STL-based generation)")
    else:
        safe_print("No thumbnail generation available (install trimesh: pip install trimesh matplotlib)")

    # Non-recursive: only *.FCStd directly in freecad_dir
    pattern = os.path.join(freecad_dir, "*.FCStd")
    fcstd_files = glob.glob(pattern)

    if not fcstd_files:
        safe_print(f"No .FCStd files found in '{freecad_dir}'")
        return

    safe_print(f"Found {len(fcstd_files)} .FCStd files in '{freecad_dir}'")

    success_count = 0
    error_count = 0

    for fcstd in fcstd_files:
        try:
            doc = FreeCAD.openDocument(fcstd)
            name = os.path.splitext(os.path.basename(fcstd))[0]

            exported = False
            for obj in doc.Objects:
                if obj.isDerivedFrom("Part::Feature") and not obj.Shape.isNull():
                    stl_path = os.path.join(exports_dir, f"{name}.stl")
                    step_path = os.path.join(exports_dir, f"{name}.step")
                    Mesh.export([obj], stl_path)
                    Part.export([obj], step_path)
                    safe_print(f"  Exported: {name}.stl + {name}.step")
                    
                    exported = True
                    success_count += 1
                    break  # first valid object

            if not exported:
                safe_print(f"  Warning: No valid Part::Feature found in {name}")

            FreeCAD.closeDocument(doc.Name)

        except Exception as e:
            error_count += 1
            safe_print(f"  Error processing file: {str(e)}")
            continue  # Skip this file, continue with next

    safe_print(f"Export complete: {success_count} models exported, {error_count} errors -> {exports_dir}/")
    
    # Generate thumbnails from STL files if trimesh is available
    if HAS_TRIMESH:
        safe_print("Generating thumbnails from STL files...")
        thumbnail_count = 0
        for stl_file in glob.glob(os.path.join(exports_dir, "*.stl")):
            name = os.path.splitext(os.path.basename(stl_file))[0]
            if generate_thumbnail_from_stl(stl_file, thumbnails_dir, name):
                thumbnail_count += 1
        safe_print(f"Generated {thumbnail_count} thumbnails -> {thumbnails_dir}/")


main()
