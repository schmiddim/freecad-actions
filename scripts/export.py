"""Export FreeCAD .FCStd files to STL and STEP formats.

Reads configuration from cad-gallery.yaml to determine which directory
to search for .FCStd files (non-recursive).

Thumbnail Rendering (in priority order):
1. OpenSCAD - Fast (~0.5s/thumbnail), good quality, requires openscad binary
2. PyRender - GPU-accelerated, best quality with correct colors
3. Matplotlib - Software rendering with proper shading (~1-2s/thumbnail), works everywhere
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

# Check for OpenSCAD (fastest rendering)
import shutil
HAS_OPENSCAD = shutil.which('openscad') is not None

# Try to import trimesh for STL-based thumbnail generation
try:
    import trimesh
    import numpy as np
    HAS_TRIMESH = True
    
    # Try to import PIL for image processing
    try:
        from PIL import Image
        HAS_PIL = True
    except ImportError:
        HAS_PIL = False
    
    # Try pyrender for better rendering (optional, fallback to trimesh)
    try:
        import pyrender
        HAS_PYRENDER = True
    except ImportError:
        HAS_PYRENDER = False
except ImportError:
    HAS_TRIMESH = False
    HAS_PIL = False
    HAS_PYRENDER = False

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
    """Generate high-quality thumbnail from STL file."""
    thumb_path = os.path.join(thumbnails_dir, f"{name}.png")
    
    #  Try OpenSCAD first (fastest)
    if HAS_OPENSCAD:
        try:
            return _render_with_openscad(stl_path, thumb_path, name)
        except Exception as e:
            safe_print(f"  OpenSCAD rendering failed: {e}, trying fallback...")
    
    # Fallback to Python renderers
    if not HAS_TRIMESH:
        safe_print(f"  No rendering backend available")
        return False
    
    try:
        mesh = trimesh.load(stl_path)
        mesh.fix_normals()
        
        max_faces = 50000
        if len(mesh.faces) > max_faces:
            safe_print(f"  Simplifying mesh ({len(mesh.faces)} -> {max_faces} faces)...")
            mesh = mesh.simplify_quadric_decimation(max_faces)
        
        if HAS_PYRENDER:
            return _render_with_pyrender(mesh, thumb_path, name)
        else:
            return _render_with_matplotlib(mesh, thumb_path, name)
        
    except Exception as e:
        safe_print(f"  Warning: STL thumbnail generation failed: {e}")
        import traceback
        safe_print(f"  {traceback.format_exc()}")
        return False


def _render_with_openscad(stl_path, thumb_path, name):
    """Render using OpenSCAD (fastest method, ~0.1s per thumbnail)."""
    import subprocess
    import tempfile
    
    # Convert to absolute path for OpenSCAD
    abs_stl_path = os.path.abspath(stl_path)
    
    # Create temporary OpenSCAD file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
        scad_file = f.name
        f.write(f"""// Auto-generated for thumbnail rendering
color([233/255, 69/255, 96/255])  // #e94560
    import("{abs_stl_path}");
""")
    
    try:
        # Check if we need xvfb for headless rendering
        has_xvfb = shutil.which('xvfb-run') is not None
        
        if has_xvfb:
            # Use xvfb-run for headless preview mode (supports colors)
            # --auto-servernum: automatically pick server number
            # -s "-screen ...": virtual screen configuration
            cmd = [
                'xvfb-run',
                '--auto-servernum',
                '--server-args=-screen 0 1024x768x24 -ac +extension GLX +render -noreset',
                'openscad',
                # NO --render flag! Preview mode supports color()
                '--camera=1,1,1,55,0,45,0',  # Isometric-like view
                '--autocenter',
                '--viewall',
                '--imgsize=800,600',
                '--projection=p',  # Perspective
                '-o', thumb_path,
                scad_file
            ]
        else:
            # Direct OpenSCAD call (for systems with display)
            cmd = [
                'openscad',
                # NO --render flag! Preview mode supports color()
                '--camera=1,1,1,55,0,45,0',  # Isometric-like view
                '--autocenter',
                '--viewall',
                '--imgsize=800,600',
                '--projection=p',  # Perspective
                '-o', thumb_path,
                scad_file
            ]
        
        # Set environment for software rendering
        env = os.environ.copy()
        env['LIBGL_ALWAYS_SOFTWARE'] = '1'
        env['GALLIUM_DRIVER'] = 'llvmpipe'
        
        # Render with timeout
        result = subprocess.run(cmd, capture_output=True, timeout=30, env=env)
        
        if result.returncode != 0:
            stderr = result.stderr.decode('utf-8', errors='replace')
            raise Exception(f"OpenSCAD exited with code {result.returncode}: {stderr}")
        
        safe_print(f"  Thumbnail: {name}.png (800x600, openscad)")
        return True
        
    finally:
        # Clean up temp file
        try:
            os.unlink(scad_file)
        except:
            pass


def _render_with_pyrender(mesh, thumb_path, name):
    """Render using pyrender (higher quality)."""
    import pyrender
    
    # Convert trimesh to pyrender mesh
    mesh_pr = pyrender.Mesh.from_trimesh(mesh)
    
    # Create scene
    scene = pyrender.Scene(ambient_light=[0.3, 0.3, 0.3], bg_color=[1.0, 1.0, 1.0, 1.0])
    scene.add(mesh_pr)
    
    # Add directional lights for better shading
    light1 = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=3.0)
    light2 = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=1.5)
    
    # Position lights
    scene.add(light1, pose=np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 5],
        [0, 0, 0, 1]
    ]))
    scene.add(light2, pose=np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, -5],
        [0, 0, 0, 1]
    ]))
    
    # Calculate camera position for isometric view
    bounds = mesh.bounds
    center = mesh.centroid
    extent = np.max(bounds[1] - bounds[0])
    
    # Camera distance (adjust to fit object)
    distance = extent * 2.0
    
    # Isometric angles: elevation=30°, azimuth=45°
    elev = np.radians(30)
    azim = np.radians(45)
    
    # Camera position in spherical coordinates
    cam_x = center[0] + distance * np.cos(elev) * np.cos(azim)
    cam_y = center[1] + distance * np.cos(elev) * np.sin(azim)
    cam_z = center[2] + distance * np.sin(elev)
    
    # Look-at matrix
    eye = np.array([cam_x, cam_y, cam_z])
    target = center
    up = np.array([0, 0, 1])
    
    # Compute camera transform
    z_axis = eye - target
    z_axis = z_axis / np.linalg.norm(z_axis)
    x_axis = np.cross(up, z_axis)
    x_axis = x_axis / np.linalg.norm(x_axis)
    y_axis = np.cross(z_axis, x_axis)
    
    camera_pose = np.eye(4)
    camera_pose[:3, 0] = x_axis
    camera_pose[:3, 1] = y_axis
    camera_pose[:3, 2] = z_axis
    camera_pose[:3, 3] = eye
    
    # Create camera
    camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0, aspectRatio=4.0/3.0)
    scene.add(camera, pose=camera_pose)
    
    # Render
    renderer = pyrender.OffscreenRenderer(800, 600)
    color, depth = renderer.render(scene)
    
    # Save image
    if HAS_PIL:
        img = Image.fromarray(color)
        img.save(thumb_path, 'PNG', optimize=True)
    else:
        import cv2
        cv2.imwrite(thumb_path, cv2.cvtColor(color, cv2.COLOR_RGB2BGR))
    
    renderer.delete()
    safe_print(f"  Thumbnail: {name}.png (800x600, pyrender)")
    return True


def _render_with_trimesh(mesh, thumb_path, name):
    """Fallback: render using trimesh native rendering or matplotlib."""
    # Try trimesh scene rendering first
    try:
        scene = mesh.scene()
        
        # Get mesh bounds for camera positioning
        bounds = mesh.bounds
        center = mesh.centroid
        extent = np.max(bounds[1] - bounds[0])
        
        # Position camera for isometric view
        distance = extent * 2.5
        
        # Isometric view angles
        elev = np.radians(30)
        azim = np.radians(45)
        
        # Camera position
        cam_x = center[0] + distance * np.cos(elev) * np.cos(azim)
        cam_y = center[1] + distance * np.cos(elev) * np.sin(azim)
        cam_z = center[2] + distance * np.sin(elev)
        
        # Create camera transform (look-at)
        eye = np.array([cam_x, cam_y, cam_z])
        target = center
        up = np.array([0, 0, 1])
        
        z_axis = eye - target
        z_axis = z_axis / np.linalg.norm(z_axis)
        x_axis = np.cross(up, z_axis)
        x_axis = x_axis / np.linalg.norm(x_axis)
        y_axis = np.cross(z_axis, x_axis)
        
        camera_transform = np.eye(4)
        camera_transform[:3, 0] = x_axis
        camera_transform[:3, 1] = y_axis
        camera_transform[:3, 2] = z_axis
        camera_transform[:3, 3] = eye
        
        scene.camera_transform = camera_transform
        
        # Render
        resolution = (800, 600)
        png_data = scene.save_image(resolution=resolution, visible=False)
        
        # Save image
        if HAS_PIL:
            from io import BytesIO
            img = Image.open(BytesIO(png_data))
            img.save(thumb_path, 'PNG', optimize=True)
        else:
            with open(thumb_path, 'wb') as f:
                f.write(png_data)
        
        safe_print(f"  Thumbnail: {name}.png (800x600, trimesh)")
        return True
        
    except Exception as e:
        # Fallback to matplotlib if trimesh rendering fails
        safe_print(f"  Trimesh rendering not available ({e}), using matplotlib...")
        return _render_with_matplotlib(mesh, thumb_path, name)


def _render_with_matplotlib(mesh, thumb_path, name):
    """Last resort: render with matplotlib (slower but works everywhere)."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        
        # Create figure
        fig = plt.figure(figsize=(8, 6), dpi=100, facecolor='white')
        ax = fig.add_subplot(111, projection='3d', facecolor='white')
        
        # Get vertices and faces
        vertices = mesh.vertices
        faces = mesh.faces
        
        # Calculate face colors with basic shading
        # Use mesh normals for lighting
        face_normals = mesh.face_normals
        light_direction = np.array([1, 1, 1])
        light_direction = light_direction / np.linalg.norm(light_direction)
        
        # Calculate lighting intensity for each face
        lighting = np.dot(face_normals, light_direction)
        lighting = np.clip(lighting, 0.2, 1.0)  # Ambient + diffuse
        
        # Base color
        base_color = np.array([0xe9/255, 0x45/255, 0x60/255])
        
        # Apply lighting to color
        face_colors = np.outer(lighting, base_color)
        face_colors = np.column_stack([face_colors, np.ones(len(faces)) * 0.95])  # Add alpha
        
        # Create 3D polygon collection
        poly3d = Poly3DCollection(
            vertices[faces],
            facecolors=face_colors,
            edgecolors='none',
            linewidths=0
        )
        ax.add_collection3d(poly3d)
        
        # Set view
        ax.view_init(elev=30, azim=45)
        
        # Set limits
        bounds = mesh.bounds
        ax.set_xlim(bounds[0][0], bounds[1][0])
        ax.set_ylim(bounds[0][1], bounds[1][1])
        ax.set_zlim(bounds[0][2], bounds[1][2])
        
        # Equal aspect ratio
        ax.set_box_aspect([
            bounds[1][0] - bounds[0][0],
            bounds[1][1] - bounds[0][1],
            bounds[1][2] - bounds[0][2]
        ])
        
        # Hide axes
        ax.set_axis_off()
        
        # Save
        fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        plt.savefig(thumb_path, dpi=100, facecolor='white', bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        
        safe_print(f"  Thumbnail: {name}.png (800x600, matplotlib)")
        return True
        
    except Exception as e:
        safe_print(f"  Matplotlib rendering failed: {e}")
        import traceback
        safe_print(f"  {traceback.format_exc()}")
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
    
    if HAS_OPENSCAD:
        safe_print("Thumbnail renderer: OpenSCAD (fast, ~0.5s per thumbnail)")
    elif HAS_TRIMESH:
        if HAS_PYRENDER:
            safe_print("Thumbnail renderer: PyRender (GPU-accelerated)")
        else:
            safe_print("Thumbnail renderer: Matplotlib (software rendering)")
        safe_print("  (install openscad for faster rendering: apt install openscad xvfb)")
    elif HAS_GUI:
        safe_print("FreeCADGui available but not used (prefer STL-based generation)")
    else:
        safe_print("No thumbnail generation available")
        safe_print("  Install: apt install openscad xvfb OR pip install trimesh matplotlib pillow")

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
    
    # Generate thumbnails from STL files if any renderer is available
    if HAS_OPENSCAD or HAS_TRIMESH:
        safe_print("Generating thumbnails from STL files...")
        thumbnail_count = 0
        for stl_file in glob.glob(os.path.join(exports_dir, "*.stl")):
            name = os.path.splitext(os.path.basename(stl_file))[0]
            if generate_thumbnail_from_stl(stl_file, thumbnails_dir, name):
                thumbnail_count += 1
        safe_print(f"Generated {thumbnail_count} thumbnails -> {thumbnails_dir}/")


main()
