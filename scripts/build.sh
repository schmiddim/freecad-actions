#!/usr/bin/env bash
# Central build script used by both Makefile and GitHub Action.
# Usage: scripts/build.sh [export|gallery|build]
#
# Environment variables:
#   DOCKER_IMAGE  - Docker image for FreeCAD export (default: ghcr.io/schmiddim/freecad-action:latest)
#   WORKSPACE     - Working directory mounted into Docker (default: current directory)
#   ACTION_PATH   - Path to the action repo (set automatically in GitHub Actions)

set -euo pipefail

DOCKER_IMAGE="${DOCKER_IMAGE:-ghcr.io/schmiddim/freecad-action:latest}"
WORKSPACE="${WORKSPACE:-$(pwd)}"
PYTHON="${PYTHON:-$(command -v python3 2>/dev/null || command -v python 2>/dev/null)}"

# Resolve script directory (for local dev) and ACTION_PATH (for CI)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ACTION_PATH="${ACTION_PATH:-$(dirname "$SCRIPT_DIR")}"

# Find a script: prefer user's repo, fall back to action's bundled copy
find_script() {
    local name="$1"
    if [ -f "${WORKSPACE}/${name}" ]; then
        echo "${WORKSPACE}/${name}"
    elif [ -f "${ACTION_PATH}/${name}" ]; then
        echo "${ACTION_PATH}/${name}"
    else
        echo >&2 "Error: ${name} not found in workspace or action path"
        exit 1
    fi
}

step_export() {
    local export_script
    export_script="$(find_script scripts/export.py)"

    echo "==> Pulling Docker image ${DOCKER_IMAGE}..."
    if ! docker pull "${DOCKER_IMAGE}" 2>/dev/null; then
        echo "==> Pull failed, building image locally..."
        docker build -t "${DOCKER_IMAGE}" "${ACTION_PATH}"
    fi

    echo "==> Exporting FCStd files to STL/STEP via Docker..."
    docker run --rm \
        -v "${WORKSPACE}:/workspace" \
        -v "${export_script}:/workspace/scripts/export.py:ro" \
        "${DOCKER_IMAGE}" \
        scripts/export.py
}

step_css() {
    # Find the scripts directory containing package.json
    local scripts_dir
    if [ -f "${WORKSPACE}/scripts/package.json" ]; then
        scripts_dir="${WORKSPACE}/scripts"
    elif [ -f "${ACTION_PATH}/scripts/package.json" ]; then
        scripts_dir="${ACTION_PATH}/scripts"
    else
        echo "==> No package.json found, skipping CSS build"
        return 0
    fi

    echo "==> Building Tailwind CSS..."
    if command -v npm >/dev/null 2>&1; then
        (cd "${scripts_dir}" && npm install --no-audit --no-fund 2>&1 | tail -1 || true)
        (cd "${scripts_dir}" && npm run build:css)
    elif command -v npx >/dev/null 2>&1; then
        (cd "${scripts_dir}" && npx tailwindcss -i ./templates/input.css -o ./templates/styles.css --minify)
    else
        echo "Warning: npm/npx not found, skipping Tailwind CSS build"
        echo "         Install Node.js to enable Tailwind CSS compilation"
    fi
}

step_gallery() {
    local gallery_script
    gallery_script="$(find_script scripts/build_gallery.py)"

    # Build CSS before gallery
    step_css

    echo "==> Installing Python dependencies..."
    "${PYTHON}" -m pip install --quiet jinja2 pyyaml 2>&1 | grep -v "syncthing-gtk" | grep -v "new release of pip" || true

    echo "==> Building gallery HTML..."
    "${PYTHON}" "${gallery_script}"
}

case "${1:-build}" in
    export)
        step_export
        ;;
    gallery)
        step_gallery
        ;;
    build)
        step_export
        step_gallery
        ;;
    *)
        echo "Usage: $0 [export|gallery|build]"
        exit 1
        ;;
esac
