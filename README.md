# CAD Gallery

Self-hosted 3D model gallery powered by FreeCAD, Three.js and GitHub Pages.

**Live Demo:** https://schmiddim.github.io/freecad-actions/

## Features

- Automatic STL export from FreeCAD `.FCStd` files
- Interactive 3D viewer with Three.js (OrbitControls)
- Metadata support: descriptions, tags, images, license, external links
- Tag-based filtering in the gallery view
- Download buttons for STL and FCStd files in the detail view
- Maker profile with About-page and links to GitHub, MakerWorld, Thingiverse, Printables
- GitHub link with icon in the navigation header
- Dark/light mode — follows system preference, toggle button on every page
- Configurable gallery title via `cad-gallery.yaml`
- Discovery document at `gallery/discovery/cad-gallery.json` (machine-readable index)
- Optional aggregator ping on every build
- Fallback display for models without metadata
- Fully buildable and testable locally via Makefile + Docker

## Project Structure

```
freecad-files/          # FreeCAD .FCStd source files (flat, no subdirs)
metadata/               # Model metadata YAML files
  my-model.yaml         # Must match FCStd filename (without extension)
  images/               # Additional images per model
    my-model/
      photo1.jpg
schemas/                # JSON Schemas for validation
  cad-gallery.schema.json  # Schema for cad-gallery.yaml
  maker.schema.json        # Schema for maker.yaml
  meta.schema.json         # Schema for metadata/*.yaml
  discovery.schema.json    # Schema for gallery/.well-known/cad-gallery.json
templates/              # Jinja2 HTML templates
  gallery.html          # Gallery overview page
  detail.html           # Model detail page with 3D viewer
  about.html            # Maker profile page
  rss.xml               # RSS feed template
  atom.xml              # Atom feed template
scripts/                # Build scripts
  export.py             # FreeCAD -> STL export
  build_gallery.py      # Generate HTML gallery from templates + metadata
  validate.py           # Validate YAML files against schemas
cad-gallery.yaml        # Configuration (paths, gallery title)
maker.yaml              # Maker profile (name, bio, links) — optional
Makefile                # Local build targets
Dockerfile              # FreeCAD Docker image for export
pyproject.toml          # Python dependencies
```

## Configuration

Edit `cad-gallery.yaml` to configure paths and the gallery title:

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/schmiddim/freecad-actions/refs/tags/v1.3.0/schemas/cad-gallery.schema.json
title: "My 3D Models"          # Optional, default: "CAD Gallery"
freecad_dir: "freecad-files"   # Where your .FCStd files are
metadata_dir: "metadata"       # Where metadata YAMLs and images are
output_dir: "gallery"          # Where the HTML gallery is generated
exports_dir: "exports"         # Where STL exports go
```

If your `.FCStd` files are in the repo root, set `freecad_dir: "."`.

## Maker Profile (Optional)

Create a `maker.yaml` in your repo root to enable the About-page and add your profile links to the navigation:

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/schmiddim/freecad-actions/refs/tags/v1.3.0/schemas/maker.schema.json
name: "Your Name"
bio: "Short description about you."
links:
  github: "https://github.com/..."
  makerworld: "https://makerworld.com/en/@..."
  thingiverse: "https://www.thingiverse.com/..."
  printables: "https://www.printables.com/@..."
```

When `maker.yaml` is present:
- An **About** page is generated at `gallery/about.html`
- An **About** link appears in the header navigation
- The **GitHub link** (with icon) appears in the header navigation

## Discovery & Aggregator

Every gallery build generates a machine-readable discovery document at:

```
gallery/discovery/cad-gallery.json
```

It contains the gallery metadata, all models (with STL/FCStd URLs, tags, license), the maker profile and the source repository URL. The schema is at [`schemas/discovery.schema.json`](schemas/discovery.schema.json).

### Aggregator Ping

To notify an aggregator service after each build, set `send-ping: 'true'` in your workflow:

```yaml
- name: Build Gallery
  uses: schmiddim/freecad-actions@v1
  with:
    send-ping: 'true'
```

The action sends a `POST` request containing `discovery_url`, `git_source_url` and `event: "push"` to a central endpoint. No configuration needed — the endpoint is built into the action.

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

Models without metadata are still displayed with a 3D preview and a hint showing which file to create.

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
make export        # Export STL from FCStd files (via Docker)
make gallery       # Build the HTML gallery (no Docker needed)
make build         # Full build: export + gallery
make serve         # Build gallery and serve at http://localhost:8000
make validate      # Validate metadata and profile YAML against schemas
make clean         # Remove generated files (exports/ and gallery/)
```

## GitHub Pages Setup

1. Go to your repo **Settings > Pages**
2. Set **Source** to **GitHub Actions**
3. Push to the `master` branch — the workflow will build and deploy automatically

## Using as a Reusable GitHub Action

This repository provides a reusable composite action to build CAD galleries from FreeCAD files.

### Minimal Setup (External Repo)

All you need is a repo with `.FCStd` files and one workflow file. No `cad-gallery.yaml`, no `templates/`, no `metadata/` — the action provides sensible defaults for everything.

**Your repo structure:**

```
my-cad-models/
  Model_A.FCStd
  Model_B.FCStd
  .github/workflows/cad-gallery.yaml
```

**The workflow file:**

```yaml
# .github/workflows/cad-gallery.yaml
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
  .github/workflows/cad-gallery.yaml
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

### Custom Configuration (Optional)

Create a `cad-gallery.yaml` in your repo root to override defaults:

```yaml
title: "My 3D Models"     # Gallery headline (default: "CAD Gallery")
freecad_dir: "."           # Where .FCStd files are (default: ".")
metadata_dir: "metadata"   # Where metadata YAMLs are (default: "metadata")
output_dir: "gallery"      # Gallery output directory (default: "gallery")
exports_dir: "exports"     # STL export directory (default: "exports")
```

### Custom Templates (Optional)

The action ships with default HTML templates. To customize the gallery appearance, create a `templates/` directory in your repo with `gallery.html`, `detail.html` and/or `about.html`. Your templates will take precedence over the defaults.

### Action Inputs

| Input | Description | Default |
|---|---|---|
| `use-docker` | Use Docker for FreeCAD export (recommended) | `true` |
| `send-ping` | Send a POST ping to the aggregator after the build | `false` |

### Action Outputs

| Output | Description |
|---|---|
| `models-count` | Number of models exported and built |

### Version Pinning

```yaml
uses: schmiddim/freecad-actions@v1       # Latest 1.x (recommended)
uses: schmiddim/freecad-actions@v1.3     # Latest 1.3.x
uses: schmiddim/freecad-actions@v1.3.0   # Exact version
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
