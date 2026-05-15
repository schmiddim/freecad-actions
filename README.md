# CAD Gallery

Self-hosted 3D model gallery powered by FreeCAD, Three.js and GitHub Pages.

**Live Demo:** https://schmiddim.github.io/freecad-actions/

## Features

- Automatic STL/STEP export from FreeCAD `.FCStd` files
- Interactive 3D viewer with Three.js (OrbitControls)
- Metadata support: descriptions, tags, images, license, external links
- Tag-based filtering in the gallery view
- Maker profile with links to MakerWorld, Thingiverse, Printables
- Fallback display for models without metadata
- Fully buildable and testable locally via Makefile + Docker

## Project Structure

```
freecad-files/          # FreeCAD .FCStd source files (flat, no subdirs)
metadata/               # Model metadata YAML files
  keycrhonev2.yaml      # Must match FCStd filename (without extension)
  images/               # Additional images per model
    keycrhonev2/
      photo1.jpg
schemas/                # JSON Schemas for validation
  meta.schema.json      # Schema for metadata/*.yaml
  profile.schema.json   # Schema for profile.yaml
templates/              # Jinja2 HTML templates
  gallery.html          # Gallery overview page
  detail.html           # Model detail page
scripts/                # Build scripts
  export.py             # FreeCAD -> STL/STEP export
  build_gallery.py      # Generate HTML gallery from templates + metadata
  validate.py           # Validate YAML files against schemas
gallery.yaml            # Configuration (paths, directories)
profile.yaml            # Maker profile (name, bio, links)
Makefile                # Local build targets
Dockerfile              # FreeCAD Docker image for export
pyproject.toml          # Python dependencies
```

## Configuration

Edit `gallery.yaml` to configure paths:

```yaml
freecad_dir: "freecad-files"   # Where your .FCStd files are
metadata_dir: "metadata"       # Where metadata YAMLs and images are
output_dir: "gallery"          # Where the HTML gallery is generated
exports_dir: "exports"         # Where STL/STEP exports go
```

If your `.FCStd` files are in the repo root, set `freecad_dir: "."`.

## Adding Model Metadata

Create a YAML file in `metadata/` matching your FCStd filename:

```yaml
# metadata/my-model.yaml
title: "My Cool Model"
description: "A detailed description of the model."
tags:
  - bracket
  - 3d-print
images:
  - filename: "photo1.jpg"
    caption: "Printed version"
license: "CC-BY-SA-4.0"
links:
  makerworld: "https://makerworld.com/en/models/..."
  printables: "https://www.printables.com/model/..."
```

Place additional images in `metadata/images/{model_name}/`.

Models without metadata will still be displayed with an STL preview and a hint showing which file to create.

## Local Development

### Prerequisites

- Docker (for FreeCAD export)
- Python 3.10+ (for gallery build)

### Setup

```bash
pip install -e ".[dev]"
```

### Makefile Targets

```bash
make help          # Show all available targets
make docker-build  # Build the FreeCAD Docker image
make export        # Export STL + STEP from FCStd files (via Docker)
make gallery       # Build the HTML gallery (no Docker needed)
make build         # Full build: export + gallery
make serve         # Build gallery and serve at http://localhost:8000
make validate      # Validate metadata and profile YAML against schemas
make clean         # Remove generated files (exports/ and gallery/)
```

## GitHub Pages Setup

1. Go to your repo **Settings > Pages**
2. Set **Source** to **GitHub Actions**
3. Push to the `master` branch -- the workflow will build and deploy automatically

## CI/CD

The GitHub Actions workflow (`.github/workflows/cad-gallery.yaml`) runs on every push to `master` or version tags (`v*`):

1. **export** -- Installs FreeCAD, exports FCStd files to STL + STEP
2. **build-gallery** -- Generates HTML gallery with metadata
3. **deploy** -- Deploys to GitHub Pages (on `master`)
4. **release** -- Creates a GitHub Release with exports (on `v*` tags)
