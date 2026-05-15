# Zielarchitektur

Selfhosted Makerworld fuer meine 3D-Modelle: FreeCAD-Dateien werden automatisch
zu STL/STEP exportiert und als interaktive Three.js Gallery auf GitHub Pages deployed.

## Umgesetzte Features (Phase 1)

- [x] **Lokaler Build via Makefile + Docker** (`make build`, `make serve`, `make validate`)
- [x] **Beschreibungen und Texte** zu FreeCAD-Dateien via `metadata/*.yaml`
- [x] **Tags pro Modell** mit Filter-Buttons in der Gallery View
- [x] **Zusaetzliche Bilder** in der Detail View via `metadata/images/{modell}/`
- [x] **Profil mit Maker-Links** (MakerWorld, Thingiverse, Printables) via `profile.yaml`
- [x] **Fallback bei fehlenden Metadaten**: STL wird gerendert + Hinweis mit konkretem Dateipfad
- [x] **Relative Links** statt hardcoded Repo-URLs
- [x] **Nicht-rekursive Suche** nach FCStd-Dateien (nur im konfigurierten Ordner)
- [x] **Eigene Container-Definition** via Dockerfile (fuer lokalen Build via Docker)
- [x] **Pages-Anleitung** in README.md dokumentiert
- [x] **Konfigurierbare Pfade** via `gallery.yaml` (funktioniert auch mit FCStd-Dateien im Root)
- [x] **JSON Schemas** zur Validierung von Metadaten und Profil
- [x] **Jinja2 Templates** statt inline HTML in Python

## Umgesetzte Features (Phase 2: Reusable Action)

- [x] **`action.yml` als reusable Composite Action** (Export + Gallery Build)
- [x] **Docker Image auf GHCR** (`ghcr.io/schmiddim/freecad-actions`)
- [x] **Multi-Stage Dockerfile** (kleineres Runtime-Image)
- [x] **Semantic Versioning** mit automatischen Moving Tags (`v1`, `v1.2`, `v1.2.3`)
- [x] **Workflow `cad-gallery.yaml` vereinfacht** (nutzt eigene Action, ~30 Zeilen statt ~100)
- [x] **Docker-Image Build+Push Workflow** (`docker-publish.yaml`)
- [x] **Release Workflow** mit automatischer GitHub Release Erstellung

## Offene Features (Phase 3+)

- [ ] RSS Feed (`gallery/feed.xml`)

## Projektstruktur

```
freecad-files/          # FreeCAD .FCStd Quelldateien (flach, keine Unterordner)
metadata/               # Metadaten-YAMLs (Name muss mit FCStd-Dateiname matchen)
  images/               # Zusaetzliche Bilder pro Modell
    {modellname}/
schemas/                # JSON Schemas fuer Validierung
  meta.schema.json
  profile.schema.json
templates/              # Jinja2 HTML Templates
  gallery.html
  detail.html
scripts/                # Build-Scripts
  export.py             # FreeCAD -> STL/STEP Export
  build_gallery.py      # HTML Gallery generieren
  validate.py           # YAML gegen Schemas validieren
gallery.yaml            # Konfiguration (Pfade)
profile.yaml            # Maker-Profil
action.yml              # Reusable Composite GitHub Action
Makefile                # Lokale Build-Targets
Dockerfile              # FreeCAD Docker Image (Multi-Stage, GHCR)
pyproject.toml          # Python Dependencies
.github/workflows/
  cad-gallery.yaml      # Gallery Build + Pages Deploy
  docker-publish.yaml   # Docker Image Build + Push zu GHCR
  release.yaml          # Semantic Versioning + GitHub Releases
  dependabot-automerge.yml
```

## Konfiguration

`gallery.yaml` steuert alle Pfade. Fuer ein Repo mit FCStd-Dateien im Root:

```yaml
freecad_dir: "."
metadata_dir: "metadata"
output_dir: "gallery"
exports_dir: "exports"
```

## Metadaten-Schema

Siehe `schemas/meta.schema.json`. Pflichtfeld ist nur `title`, alles andere optional:

```yaml
title: "Modellname"
description: "Beschreibung (Markdown)"
tags: [tag1, tag2]
images:
  - filename: "foto.jpg"
    caption: "Beschreibung"
links:
  makerworld: "https://..."
  printables: "https://..."
license: "CC-BY-SA-4.0"
```
