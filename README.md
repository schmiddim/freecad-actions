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

## Using as a Reusable GitHub Action

This repository provides a reusable composite action to build CAD galleries from FreeCAD files.

### Minimal Setup (External Repo)

All you need is a repo with `.FCStd` files and one workflow file. No `gallery.yaml`, no `templates/`, no `metadata/` -- the action provides sensible defaults for everything.

**Your repo structure:**

```
my-cad-models/
  Model_A.FCStd
  Model_B.FCStd
  .github/workflows/gallery.yaml
```

**The workflow file:**

```yaml
# .github/workflows/gallery.yaml
name: CAD Gallery

on:
  push:
    branches: [main]

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deploy.outputs.page_url }}
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0

      - name: Build Gallery
        uses: schmiddim/freecad-actions@v1

      - uses: actions/configure-pages@v6

      - uses: actions/upload-pages-artifact@v5
        with:
          path: ./gallery

      - id: deploy
        uses: actions/deploy-pages@v5
```

**Prerequisites:** Enable GitHub Pages in your repo settings (Settings > Pages > Source: GitHub Actions).

### Adding Metadata (Optional)

To add descriptions, tags, images and links to your models, create metadata YAML files:

```
my-cad-models/
  Model_A.FCStd
  metadata/
    Model_A.yaml        # Must match FCStd filename
    images/
      Model_A/
        photo1.jpg
  .github/workflows/gallery.yaml
```

```yaml
# metadata/Model_A.yaml
title: "My Cool Model"
description: "A bracket for mounting stuff."
tags: [bracket, 3d-print]
license: "CC-BY-SA-4.0"
images:
  - filename: "photo1.jpg"
    caption: "Printed version"
links:
  printables: "https://www.printables.com/model/..."
```

Models without metadata are still displayed with a 3D preview and a hint showing which file to create.

### Custom Configuration (Optional)

Create a `gallery.yaml` in your repo root to override defaults:

```yaml
freecad_dir: "."           # Where .FCStd files are (default: ".")
metadata_dir: "metadata"   # Where metadata YAMLs are (default: "metadata")
output_dir: "gallery"      # Gallery output directory (default: "gallery")
exports_dir: "exports"     # STL/STEP export directory (default: "exports")
```

### Custom Templates (Optional)

The action ships with default HTML templates. To customize the gallery appearance, create a `templates/` directory in your repo with `gallery.html` and/or `detail.html`. Your templates will take precedence over the defaults.

### Action Inputs

| Input | Description | Default |
|---|---|---|
| `use-docker` | Use Docker for FreeCAD export (recommended) | `true` |

### Action Outputs

| Output | Description |
|---|---|
| `models-count` | Number of models exported and built |

### Version Pinning

```yaml
uses: schmiddim/freecad-actions@v1       # Latest 1.x (recommended)
uses: schmiddim/freecad-actions@v1.2     # Latest 1.2.x
uses: schmiddim/freecad-actions@v1.2.3   # Exact version
```

## CI/CD

### Workflows

| Workflow | Trigger | Purpose |
|---|---|---|
| `cad-gallery.yaml` | Push to `master` | Build gallery + deploy to GitHub Pages |
| `docker-publish.yaml` | Push to `master` (Dockerfile changes) or Release | Build + push Docker image to GHCR |
| `release.yaml` | Version tag (`v*.*.*`) | Create GitHub Release + moving version tags |
| `dependabot-automerge.yml` | Dependabot PR | Auto-merge dependency updates |

### Docker Image

The FreeCAD export container is hosted on GitHub Container Registry:

```bash
docker pull ghcr.io/schmiddim/freecad-actions:latest
```
