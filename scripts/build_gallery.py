"""Build the CAD Gallery HTML pages from exported STL files and metadata.

Reads configuration from cad-gallery.yaml, loads metadata from the metadata
directory, and generates HTML pages using Jinja2 templates.
"""

import json
import os
import sys
import glob
import shutil
import subprocess
from datetime import datetime
from email.utils import formatdate

import yaml
from jinja2 import Environment, FileSystemLoader

# Ensure UTF-8 encoding for stdout/stderr
if sys.version_info >= (3, 7):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass
else:
    # Fallback for older Python versions
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')
    except:
        pass


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
    config_path = "cad-gallery.yaml"
    defaults = {
        "freecad_dir": ".",
        "metadata_dir": "metadata",
        "output_dir": "gallery",
        "exports_dir": "exports",
    }

    if not os.path.exists(config_path):
        # Fallback to old name for backwards compatibility
        config_path = "gallery.yaml"

    if not os.path.exists(config_path):
        safe_print("Warning: cad-gallery.yaml not found, using defaults")
        return defaults

    with open(config_path) as f:
        cfg = yaml.safe_load(f) or {}

    merged = {**defaults, **cfg}
    if not merged.get("title"):
        merged["title"] = "CAD Gallery"
    return merged


def load_profile():
    """Load maker.yaml if it exists. Returns None if not found (profile is optional)."""
    for path in ("maker.yaml", "profile.yaml"):
        if os.path.exists(path):
            with open(path) as f:
                return yaml.safe_load(f)
    return None


def load_metadata(metadata_dir, model_name):
    """Load metadata for a model. Returns (metadata_dict, has_metadata)."""
    for ext in (".yaml", ".yml"):
        meta_path = os.path.join(metadata_dir, f"{model_name}{ext}")
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                data = yaml.safe_load(f)
            if data:
                return data, True

    return {}, False


def get_git_commit_date(filepath):
    """Get the last git commit date for a file as a Unix timestamp."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", filepath],
            capture_output=True,
            text=True,
            check=True,
        )
        timestamp = result.stdout.strip()
        if timestamp:
            return int(timestamp)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return None


def collect_models(config):
    """Collect all models with their metadata and dates."""
    freecad_dir = config["freecad_dir"]
    metadata_dir = config["metadata_dir"]
    exports_dir = config["exports_dir"]

    # Build index of FCStd files with their git commit dates
    fcstd_dates = {}
    pattern = os.path.join(freecad_dir, "*.FCStd")
    for fcstd in glob.glob(pattern):
        name = os.path.splitext(os.path.basename(fcstd))[0]
        git_date = get_git_commit_date(fcstd)
        if git_date:
            mtime = git_date
        else:
            mtime = int(os.path.getmtime(fcstd))

        if name not in fcstd_dates or mtime > fcstd_dates[name]:
            fcstd_dates[name] = mtime

    safe_print(f"Found {len(fcstd_dates)} FCStd files in '{freecad_dir}'")

    # Collect models from exported STL files
    models = []
    for stl in glob.glob(os.path.join(exports_dir, "*.stl")):
        name = os.path.splitext(os.path.basename(stl))[0]

        # Get date
        if name in fcstd_dates:
            mtime = fcstd_dates[name]
        else:
            mtime = int(os.path.getmtime(stl))
            safe_print(f"  Warning: No FCStd found for '{name}', using STL date")

        # Load metadata
        meta, has_metadata = load_metadata(metadata_dir, name)

        # Build metadata file path hint for the fallback message
        metadata_path = os.path.join(metadata_dir, f"{name}.yaml")

        model = {
            "name": name,
            "stl": f"models/{name}.stl",
            "mtime": mtime,
            "title": meta.get("title", name),
            "description": meta.get("description", ""),
            "tags": meta.get("tags", []),
            "images": meta.get("images", []),
            "links": meta.get("links", {}),
            "license": meta.get("license", ""),
            "has_metadata": has_metadata,
            "metadata_path": metadata_path,
        }
        models.append(model)

    # Sort newest first
    models.sort(key=lambda x: x["mtime"], reverse=True)

    safe_print(f"Collected {len(models)} models (sorted by date, newest first)")
    for m in models[:5]:
        status = "with metadata" if m["has_metadata"] else "NO metadata"
        safe_print(f"  {m['name']}: {m['mtime']} ({status})")

    return models


def collect_all_tags(models):
    """Collect all unique tags across all models, sorted alphabetically."""
    tags = set()
    for model in models:
        tags.update(model.get("tags", []))
    return sorted(tags)


def copy_assets(config, metadata_dir):
    """Copy STL files and metadata images to the output directory."""
    output_dir = config["output_dir"]
    exports_dir = config["exports_dir"]

    # Copy STL files
    models_dir = os.path.join(output_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    for stl in glob.glob(os.path.join(exports_dir, "*.stl")):
        shutil.copy(stl, models_dir)

    # Copy metadata images
    images_src = os.path.join(metadata_dir, "images")
    if os.path.isdir(images_src):
        images_dst = os.path.join(output_dir, "images")
        if os.path.exists(images_dst):
            shutil.rmtree(images_dst)
        shutil.copytree(images_src, images_dst)
        safe_print(f"Copied images from '{images_src}' to '{images_dst}'")


def find_templates_dir():
    """Find the templates directory.

    Lookup order:
      1. ./templates  (user's repo has custom templates)
      2. $ACTION_PATH/templates  (bundled default templates from the action)
      3. Directory of this script/../templates  (local dev / Makefile usage)

    Returns the first existing path, or raises FileNotFoundError.
    """
    candidates = ["templates"]

    action_path = os.environ.get("ACTION_PATH")
    if action_path:
        candidates.append(os.path.join(action_path, "templates"))

    # Fallback: relative to this script (for local dev / Makefile)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.join(script_dir, "..", "templates"))

    for candidate in candidates:
        resolved = os.path.realpath(candidate)
        if os.path.isdir(resolved):
            safe_print(f"Using templates from: {resolved}")
            return resolved

    msg = "No templates directory found. Searched:\n" + "\n".join(f"  - {c}" for c in candidates)
    raise FileNotFoundError(msg)


def build_gallery(config, models, profile):
    """Build the gallery HTML pages using Jinja2 templates."""
    output_dir = config["output_dir"]
    metadata_dir = config["metadata_dir"]

    # Setup Jinja2 — find templates in repo or fall back to action defaults
    templates_dir = find_templates_dir()
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=False,
    )

    # Prepare output directories
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "view"), exist_ok=True)

    # Copy assets
    copy_assets(config, metadata_dir)

    # Collect all tags for filter buttons
    all_tags = collect_all_tags(models)

    # Build models_json for the JavaScript thumbnail renderer
    models_json = json.dumps(
        [{"name": m["name"], "stl": m["stl"]} for m in models]
    )

    # Render index page
    gallery_template = env.get_template("gallery.html")
    index_html = gallery_template.render(
        models=models,
        models_json=models_json,
        profile=profile,
        all_tags=all_tags,
    )
    index_path = os.path.join(output_dir, "index.html")
    with open(index_path, "w") as f:
        f.write(index_html)

    # Render detail pages
    detail_template = env.get_template("detail.html")
    for i, model in enumerate(models):
        prev_model = models[i - 1] if i > 0 else None
        next_model = models[i + 1] if i < len(models) - 1 else None

        detail_html = detail_template.render(
            model=model,
            prev_model=prev_model,
            next_model=next_model,
        )
        detail_path = os.path.join(output_dir, "view", f"{model['name']}.html")
        with open(detail_path, "w") as f:
            f.write(detail_html)

    safe_print(f"Gallery built: index.html + {len(models)} detail pages in '{output_dir}/'")


def format_rfc822(timestamp):
    """Convert Unix timestamp to RFC 822 date format (for RSS)."""
    return formatdate(timestamp, usegmt=True)


def format_iso8601(timestamp):
    """Convert Unix timestamp to ISO 8601 format (for Atom)."""
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%SZ')


def get_base_url():
    """Derive base URL from git remote or environment variable.
    
    Priority:
      1. GALLERY_BASE_URL env var (user-provided)
      2. Extract from git remote (github.com/user/repo -> https://user.github.io/repo)
      3. Fallback to localhost
    """
    base_url = os.environ.get('GALLERY_BASE_URL')
    if base_url:
        return base_url.rstrip('/')
    
    try:
        result = subprocess.run(
            ['git', 'config', '--get', 'remote.master.url'],
            capture_output=True, text=True, check=True
        )
        remote = result.stdout.strip()
        
        # Parse: git@github.com:user/repo.git or https://github.com/user/repo
        if 'github.com' in remote:
            # Extract user and repo from various git URL formats
            parts = remote.replace(':', '/').replace('.git', '').split('/')
            user = parts[-2]
            repo = parts[-1]
            return f'https://{user}.github.io/{repo}'
    except:
        # Try origin as fallback
        try:
            result = subprocess.run(
                ['git', 'config', '--get', 'remote.origin.url'],
                capture_output=True, text=True, check=True
            )
            remote = result.stdout.strip()
            if 'github.com' in remote:
                parts = remote.replace(':', '/').replace('.git', '').split('/')
                user = parts[-2]
                repo = parts[-1]
                return f'https://{user}.github.io/{repo}'
        except:
            pass
    
    return 'http://localhost:8000'  # Fallback


def build_feeds(config, models, profile):
    """Build RSS and Atom feeds."""
    output_dir = config["output_dir"]
    templates_dir = find_templates_dir()
    
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=False,
    )
    
    # Custom filters for date formatting
    env.filters['format_rfc822'] = format_rfc822
    env.filters['format_iso8601'] = format_iso8601
    
    base_url = get_base_url()
    
    # Render RSS feed
    rss_template = env.get_template('rss.xml')
    rss_content = rss_template.render(
        models=models,
        profile=profile,
        base_url=base_url,
    )
    rss_path = os.path.join(output_dir, 'rss.xml')
    with open(rss_path, 'w') as f:
        f.write(rss_content)
    
    # Render Atom feed
    atom_template = env.get_template('atom.xml')
    atom_content = atom_template.render(
        models=models,
        profile=profile,
        base_url=base_url,
        now=int(datetime.now().timestamp()),
    )
    atom_path = os.path.join(output_dir, 'atom.xml')
    with open(atom_path, 'w') as f:
        f.write(atom_content)
    
    safe_print(f"Feeds built: rss.xml + atom.xml ({len(models)} models, base URL: {base_url})")


def main():
    config = load_config()
    profile = load_profile()
    models = collect_models(config)

    if not models:
        safe_print("No models found. Make sure STL exports exist.")
        return

    build_gallery(config, models, profile)
    build_feeds(config, models, profile)


if __name__ == "__main__":
    main()
