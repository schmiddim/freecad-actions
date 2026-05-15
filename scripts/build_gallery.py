import os, glob, shutil, json, subprocess

# Kopiere exports in gallery für GitHub Pages
os.makedirs("gallery/models", exist_ok=True)
for stl in glob.glob("exports/*.stl"):
    shutil.copy(stl, "gallery/models/")

def get_git_commit_date(filepath):
    """Holt das letzte Git-Commit-Datum einer Datei als Unix-Timestamp."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", filepath],
            capture_output=True, text=True, check=True
        )
        timestamp = result.stdout.strip()
        if timestamp:
            return int(timestamp)
    except:
        pass
    return None

# Baue Index aller FCStd-Dateien mit ihren Git-Commit-Daten
fcstd_dates = {}
for fcstd in glob.glob("**/*.FCStd", recursive=True):
    name = os.path.splitext(os.path.basename(fcstd))[0]
    
    # Git-Commit-Datum verwenden
    git_date = get_git_commit_date(fcstd)
    if git_date:
        mtime = git_date
    else:
        # Fallback: Filesystem-mtime
        mtime = int(os.path.getmtime(fcstd))
    
    # Falls mehrere FCStd mit gleichem Namen, nimm die neueste
    if name not in fcstd_dates or mtime > fcstd_dates[name]:
        fcstd_dates[name] = mtime

print(f"Found {len(fcstd_dates)} FCStd files with dates")

# Sammle Modelle - Sortierung nach FCStd-Datum
models = []
for stl in glob.glob("exports/*.stl"):
    name = os.path.splitext(os.path.basename(stl))[0]
    
    # Nutze FCStd-Datum wenn vorhanden
    if name in fcstd_dates:
        mtime = fcstd_dates[name]
    else:
        mtime = int(os.path.getmtime(stl))
        print(f"Warning: No FCStd found for {name}, using STL date")
    
    models.append({"name": name, "stl": f"models/{name}.stl", "mtime": mtime})

models.sort(key=lambda x: x["mtime"], reverse=True)

# Debug: Zeige erste 5 Modelle
print("Top 5 models (newest first):")
for m in models[:5]:
    print(f"  {m['name']}: {m['mtime']}")

# Gemeinsame Styles
common_styles = """
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { 
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #1a1a2e; 
      color: #eee;
      min-height: 100vh;
    }
    header {
      background: #16213e;
      padding: 1.5rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #0f3460;
    }
    header h1 { font-size: 1.5rem; font-weight: 600; }
    header a { 
      color: #94a3b8; 
      text-decoration: none; 
      font-size: 0.9rem;
      transition: color 0.2s;
    }
    header a:hover { color: #fff; }
    .btn {
      background: #0f3460;
      color: #fff;
      border: none;
      padding: 0.75rem 1.5rem;
      border-radius: 8px;
      cursor: pointer;
      font-size: 0.9rem;
      text-decoration: none;
      transition: background 0.2s;
      display: inline-block;
    }
    .btn:hover { background: #1a4a7a; }
    .btn-primary { background: #e94560; }
    .btn-primary:hover { background: #ff6b6b; }
"""

# Index-Seite (Grid mit Thumbnails)
models_json = json.dumps([{"name": m["name"], "stl": m["stl"]} for m in models])

index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CAD Gallery</title>
  <script type="importmap">
    {{
      "imports": {{
        "three": "https://cdn.jsdelivr.net/npm/three@0.165.0/build/three.module.js",
        "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.165.0/examples/jsm/"
      }}
    }}
  </script>
  <style>
{common_styles}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1.5rem;
      padding: 2rem;
      max-width: 1600px;
      margin: 0 auto;
    }}
    .card {{
      background: #16213e;
      border-radius: 12px;
      overflow: hidden;
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
      border: 1px solid #0f3460;
      text-decoration: none;
      color: inherit;
      display: block;
    }}
    .card:hover {{
      transform: translateY(-4px);
      box-shadow: 0 12px 40px rgba(0,0,0,0.4);
    }}
    .thumbnail {{
      width: 100%;
      height: 200px;
      background: #0f0f23;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }}
    .thumbnail img {{
      width: 100%;
      height: 100%;
      object-fit: contain;
    }}
    .thumbnail .loading {{
      color: #4a5568;
      font-size: 0.8rem;
    }}
    .card-info {{
      padding: 1rem;
      border-top: 1px solid #0f3460;
    }}
    .card-info h3 {{
      font-size: 0.9rem;
      font-weight: 500;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
  </style>
</head>
<body>
  <header>
    <h1>CAD Gallery</h1>
    <a href="https://github.com/schmiddim/freecad" target="_blank">View on GitHub</a>
  </header>
  
  <div class="grid" id="grid"></div>

<script type="module">
import * as THREE from 'three';
import {{ STLLoader }} from 'three/addons/loaders/STLLoader.js';

const models = {models_json};
const loader = new STLLoader();
const grid = document.getElementById('grid');

// Shared offscreen renderer for thumbnails
let thumbRenderer = null;
let thumbScene = null;
let thumbCamera = null;

function initThumbRenderer() {{
  thumbRenderer = new THREE.WebGLRenderer({{ antialias: true, preserveDrawingBuffer: true }});
  thumbRenderer.setSize(400, 300);
  thumbRenderer.setPixelRatio(1);
  
  thumbScene = new THREE.Scene();
  thumbScene.background = new THREE.Color(0x0f0f23);
  
  thumbCamera = new THREE.PerspectiveCamera(45, 400/300, 0.1, 1000);
  
  thumbScene.add(new THREE.AmbientLight(0x404040, 3));
  const dirLight = new THREE.DirectionalLight(0xffffff, 1);
  dirLight.position.set(1, 1, 1);
  thumbScene.add(dirLight);
  const dirLight2 = new THREE.DirectionalLight(0xffffff, 0.5);
  dirLight2.position.set(-1, -1, -1);
  thumbScene.add(dirLight2);
}}

function renderThumbnail(stlPath, callback) {{
  if (!thumbRenderer) initThumbRenderer();
  
  loader.load(stlPath, geometry => {{
    // Clear previous mesh
    const toRemove = thumbScene.children.filter(c => c.type === 'Mesh');
    toRemove.forEach(m => thumbScene.remove(m));
    
    const material = new THREE.MeshStandardMaterial({{ 
      color: 0xe94560, 
      metalness: 0.3, 
      roughness: 0.6 
    }});
    const mesh = new THREE.Mesh(geometry, material);
    
    geometry.computeBoundingBox();
    const center = geometry.boundingBox.getCenter(new THREE.Vector3());
    const size = geometry.boundingBox.getSize(new THREE.Vector3());
    mesh.position.sub(center);
    mesh.rotation.x = -0.5;
    mesh.rotation.y = 0.5;
    
    thumbScene.add(mesh);
    thumbCamera.position.set(0, 0, Math.max(size.x, size.y, size.z) * 2.5);
    thumbCamera.lookAt(0, 0, 0);
    
    thumbRenderer.render(thumbScene, thumbCamera);
    
    const dataUrl = thumbRenderer.domElement.toDataURL('image/png');
    callback(dataUrl);
    
    // Cleanup
    geometry.dispose();
    material.dispose();
  }});
}}

// Build grid
models.forEach((model, i) => {{
  const card = document.createElement('a');
  card.className = 'card';
  card.href = `view/${{model.name}}.html`;
  card.innerHTML = `
    <div class="thumbnail" id="thumb-${{i}}">
      <span class="loading">Loading...</span>
    </div>
    <div class="card-info">
      <h3>${{model.name}}</h3>
    </div>
  `;
  grid.appendChild(card);
}});

// Lazy load thumbnails
const observer = new IntersectionObserver((entries) => {{
  entries.forEach(entry => {{
    if (entry.isIntersecting) {{
      const card = entry.target;
      const thumb = card.querySelector('.thumbnail');
      const name = card.href.split('/').pop().replace('.html', '');
      const model = models.find(m => m.name === name);
      
      if (thumb && model && !thumb.dataset.loaded) {{
        thumb.dataset.loaded = 'true';
        renderThumbnail(model.stl, (dataUrl) => {{
          thumb.innerHTML = `<img src="${{dataUrl}}" alt="${{model.name}}">`;
        }});
      }}
      observer.unobserve(card);
    }}
  }});
}}, {{ rootMargin: '200px' }});

document.querySelectorAll('.card').forEach(card => observer.observe(card));
</script>
</body>
</html>"""

with open("gallery/index.html", "w") as f:
    f.write(index_html)

# Detail-Seiten für jedes Modell
os.makedirs("gallery/view", exist_ok=True)

for i, model in enumerate(models):
    # Vorheriges/Nächstes Modell für Navigation
    prev_model = models[i - 1] if i > 0 else None
    next_model = models[i + 1] if i < len(models) - 1 else None
    
    nav_html = '<div class="nav">'
    if prev_model:
        nav_html += f'<a href="{prev_model["name"]}.html" class="btn">Previous</a>'
    else:
        nav_html += '<span></span>'
    nav_html += f'<a href="../index.html" class="btn">Back to Gallery</a>'
    if next_model:
        nav_html += f'<a href="{next_model["name"]}.html" class="btn">Next</a>'
    else:
        nav_html += '<span></span>'
    nav_html += '</div>'
    
    detail_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{model["name"]} - CAD Gallery</title>
  <script type="importmap">
    {{
      "imports": {{
        "three": "https://cdn.jsdelivr.net/npm/three@0.165.0/build/three.module.js",
        "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.165.0/examples/jsm/"
      }}
    }}
  </script>
  <style>
{common_styles}
    .container {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 2rem;
    }}
    .viewer-wrapper {{
      background: #0f0f23;
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid #0f3460;
    }}
    .viewer {{
      width: 100%;
      height: 70vh;
      min-height: 400px;
    }}
    .viewer canvas {{
      width: 100%;
      height: 100%;
    }}
    .info {{
      padding: 1.5rem;
      border-top: 1px solid #0f3460;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }}
    .info h2 {{
      font-size: 1.3rem;
      font-weight: 600;
    }}
    .nav {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 1.5rem;
      gap: 1rem;
    }}
    .nav .btn {{
      min-width: 120px;
      text-align: center;
    }}
    .loading {{
      display: flex;
      align-items: center;
      justify-content: center;
      height: 70vh;
      color: #4a5568;
    }}
  </style>
</head>
<body>
  <header>
    <h1>CAD Gallery</h1>
    <a href="https://github.com/schmiddim/freecad" target="_blank">View on GitHub</a>
  </header>
  
  <div class="container">
    <div class="viewer-wrapper">
      <div class="viewer" id="viewer">
        <div class="loading">Loading 3D model...</div>
      </div>
      <div class="info">
        <h2>{model["name"]}</h2>
        <a href="../{model["stl"]}" download class="btn btn-primary">Download STL</a>
      </div>
    </div>
    {nav_html}
  </div>

<script type="module">
import * as THREE from 'three';
import {{ STLLoader }} from 'three/addons/loaders/STLLoader.js';
import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';

const container = document.getElementById('viewer');
const width = container.clientWidth;
const height = container.clientHeight;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0f0f23);

const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 10000);
const renderer = new THREE.WebGLRenderer({{ antialias: true }});
renderer.setSize(width, height);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

container.innerHTML = '';
container.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;

// Lighting
scene.add(new THREE.AmbientLight(0x404040, 3));
const dirLight = new THREE.DirectionalLight(0xffffff, 1);
dirLight.position.set(1, 1, 1);
scene.add(dirLight);
const dirLight2 = new THREE.DirectionalLight(0xffffff, 0.5);
dirLight2.position.set(-1, -1, -1);
scene.add(dirLight2);

// Load model
const loader = new STLLoader();
loader.load('../{model["stl"]}', geometry => {{
  const material = new THREE.MeshStandardMaterial({{ 
    color: 0xe94560, 
    metalness: 0.3, 
    roughness: 0.6 
  }});
  const mesh = new THREE.Mesh(geometry, material);
  
  geometry.computeBoundingBox();
  const center = geometry.boundingBox.getCenter(new THREE.Vector3());
  const size = geometry.boundingBox.getSize(new THREE.Vector3());
  mesh.position.sub(center);
  
  scene.add(mesh);
  camera.position.set(0, 0, Math.max(size.x, size.y, size.z) * 2.5);
  controls.update();
}});

// Animation loop
function animate() {{
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}}
animate();

// Resize handler
window.addEventListener('resize', () => {{
  const w = container.clientWidth;
  const h = container.clientHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
}});
</script>
</body>
</html>"""
    
    with open(f"gallery/view/{model['name']}.html", "w") as f:
        f.write(detail_html)

print(f"Gallery built with {len(models)} models (sorted by date, newest first).")
print(f"Created index.html + {len(models)} detail pages in view/")
