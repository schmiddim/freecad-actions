#!/usr/bin/env bash
# Central build script used by both Makefile and GitHub Action.
# Usage: scripts/build.sh [export|gallery|build]
#
# Environment variables:
#   DOCKER_IMAGE  - Docker image for FreeCAD export (default: ghcr.io/schmiddim/freecad-actions:latest)
#   WORKSPACE     - Working directory mounted into Docker (default: current directory)

set -euo pipefail

DOCKER_IMAGE="${DOCKER_IMAGE:-ghcr.io/schmiddim/freecad-actions:latest}"
WORKSPACE="${WORKSPACE:-$(pwd)}"
PYTHON="${PYTHON:-$(command -v python3 2>/dev/null || command -v python 2>/dev/null)}"

step_export() {
    echo "==> Exporting FCStd files to STL/STEP via Docker..."
    docker run --rm \
        -v "${WORKSPACE}:/workspace" \
        "${DOCKER_IMAGE}" \
        scripts/export.py
}

step_gallery() {
    echo "==> Installing Python dependencies..."
    "${PYTHON}" -m pip install --quiet jinja2 pyyaml

    echo "==> Building gallery HTML..."
    "${PYTHON}" scripts/build_gallery.py
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
