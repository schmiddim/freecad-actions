# AGENTS.md

## What this is

GitHub Action + self-hosted 3D model gallery. FreeCAD `.FCStd` files are exported to STL via Docker, then Jinja2 templates produce a static HTML gallery with a Three.js viewer. Deployed to GitHub Pages.

## Repository layout

```
scripts/
  build_gallery.py    # Main build: templates + metadata -> HTML gallery
  export.py           # FreeCAD -> STL export (runs inside Docker)
  validate.py         # YAML schema validation
  build.sh            # Entrypoint used by Makefile and action.yml
  templates/          # Jinja2 templates + styles.css
    gallery.html      # Index page
    detail.html       # Model detail with 3D viewer
    about.html        # Maker profile (only if maker.yaml exists)
    styles.css        # All CSS (shared across pages)
    rss.xml / atom.xml
schemas/              # JSON Schemas for all YAML configs
freecad-files/        # Source .FCStd files (flat)
metadata/             # Per-model YAML + images/
cad-gallery.yaml      # Gallery config (title, paths)
maker.yaml            # Optional maker profile
action.yml            # Composite GitHub Action definition
Dockerfile            # FreeCAD export container (conda + debian)
```

## Key commands

```bash
# Install Python deps (jinja2, pyyaml, jsonschema)
pip install -e ".[dev]"

# Full build: Docker export + gallery HTML
make build

# Gallery only (no Docker, no FreeCAD export - fast iteration on templates)
python3 scripts/build_gallery.py

# Serve locally after build
make serve   # http://localhost:8000

# Validate YAML against schemas
make validate
```

`make build` requires Docker. `python3 scripts/build_gallery.py` does not.

## Template system

- Templates are in `scripts/templates/` (moved from root `templates/` in v2.6.0)
- `build_gallery.py` finds templates via `find_templates_dir()` which checks:
  1. `scripts/templates/` (repo default)
  2. `$ACTION_PATH/templates/` (when used as a reusable action by other repos)
  3. `<script_dir>/templates/` (fallback for local dev)
- All CSS is in `styles.css` - no inline styles in HTML templates
- `styles.css` is auto-copied to the output directory during build
- Gallery/detail pages: `href="styles.css"` / `href="../styles.css"` (detail pages live in `view/`)
- Templates use Jinja2. Key variables passed to all pages: `title`, `profile`, `git_source_url`
- Header GitHub link points to the **repository** (`git_source_url`), not the user profile
- About page keeps the **user profile** link from `profile.links.github`

## Release process

1. Commit with conventional commits (`feat:`, `fix:`, `refactor:`)
2. Create annotated tag: `git tag -a v2.X.0 -m "Release v2.X.0 ..."`
3. Push commit + tag: `git push master master && git push master v2.X.0`
4. CI does the rest:
   - `release.yaml` creates GitHub Release with auto-generated notes + moving tags (`v2`, `v2.X`)
   - `docker-publish.yaml` rebuilds and pushes the Docker image to GHCR

**Note:** The git remote is named `master`, not `origin`.

## Gotchas

- **Remote name:** `git remote` is `master`, not `origin`. Push with `git push master master`.
- **`get_base_url()`** in `build_gallery.py` tries `remote.master.url` first, then falls back to `remote.origin.url`. Both are checked.
- **`git_source_url`** is derived at build time from the git remote. Returns `None` when no remote exists (local dev without remote). Templates guard with `{% if git_source_url %}`.
- **Schema URLs** in `cad-gallery.yaml` and `maker.yaml` reference pinned release tags. Update them when schemas change and a new release is cut.
- **Docker image:** `ghcr.io/schmiddim/freecad-action:latest`. The `build.sh` script auto-pulls it; if pull fails, it builds locally.
- **`export.py` runs inside FreeCAD's embedded Python** (`freecadcmd`), not standard Python. It cannot use pip packages.
- **Output directory:** `gallery/` is gitignored and fully regenerated on each build. Never edit files there.
- **Default branch** is `master`, not `main`.
