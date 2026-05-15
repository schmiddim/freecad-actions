# Zielarchitektur

Selfhosted Makerworld fuer meine 3D-Modelle: FreeCAD-Dateien werden automatisch
zu STL/STEP exportiert und als interaktive Three.js Gallery auf GitHub Pages deployed.

## Umgesetzte Features (Phase 1)

- [x] **Lokaler Build via Makefile + Docker** (`make build`, `make serve`, `make validate`)
- [x] **Beschreibungen und Texte** zu FreeCAD-Dateien via `metadata/*.yaml`
- [x] **Tags pro Modell** mit Filter-Buttons in der Gallery View
- [x] **Zusaetzliche Bilder** in der Detail View via `metadata/images/{modell}/`
- [x] **Profil mit Maker-Links** (MakerWorld, Thingiverse, Printables) via `maker.yaml`
- [x] **Fallback bei fehlenden Metadaten**: STL wird gerendert + Hinweis mit konkretem Dateipfad
- [x] **Relative Links** statt hardcoded Repo-URLs
- [x] **Nicht-rekursive Suche** nach FCStd-Dateien (nur im konfigurierten Ordner)
- [x] **Eigene Container-Definition** via Dockerfile (fuer lokalen Build via Docker)
- [x] **Pages-Anleitung** in README.md dokumentiert
- [x] **Konfigurierbare Pfade** via `cad-gallery.yaml` (funktioniert auch mit FCStd-Dateien im Root)
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
- [x] RSS Feed (`gallery/rss.xml`) + Atom Feed (`gallery/atom.xml`)

## Umgesetzte Features (Phase 4: Details & Customization)

- [x] **Konfigurierbare Gallery-Headline** via `title`-Feld in `cad-gallery.yaml`
    - Fallback: `"CAD Gallery"` wenn nicht gesetzt
    - Titel wird in allen Templates verwendet (Browser-Titel, H1)
- [x] **About-Page** (`gallery/about.html`)
    - Generiert aus `maker.yaml`: name, bio, alle Links
    - Optionales Avatar-Bild
    - Navigation-Link "About" in Header aller Seiten (nur wenn `maker.yaml` vorhanden)
    - Kein About-Link und keine About-Page wenn `maker.yaml` fehlt
- [x] **GitHub-Link im Header** (mit GitHub-Icon, aus `maker.yaml → links.github`)
    - Auf allen Seiten sichtbar, nur wenn `profile.links.github` gesetzt
- [x] **Download FCStd in Detail-View**
    - Button "Download FCStd" neben "Download STL" (nur wenn FCStd-Datei vorhanden)
    - FCStd-Dateien werden nach `gallery/freecad/` kopiert
- [x] **Dark/Light-Mode** auf allen Seiten
    - Erkennt automatisch System-Praeferenz (`prefers-color-scheme`)
    - Toggle-Button (🌙 / ☀️) im Header
    - Wahl wird in `localStorage` gespeichert (bleibt nach Reload erhalten)
    - CSS Custom Properties (`--bg`, `--surface`, `--border`, `--text`, `--muted`, `--accent`)
    - Kein Flash beim Laden (Theme-Initialisierung im `<head>` vor dem Render)

## Offene Features (Phase 3+)

- [ ] Tests (z.B. Python unit tests fuer `build_gallery.py`, `validate.py`)
- [ ] Publish mit Release-Trigger
- [ ] Server-Teil (Aggregator-Backend)

## Offene Features (Phase 5: Aggregator-Integration)

- [ ] **`gallery/.well-known/cad-gallery.json` generieren** (`build_gallery.py`)
    - Felder: `version`, `generator`, `generator_version` (aus `ACTION_REF` Env)
    - `profile`: name, bio, links (aus `maker.yaml`)
    - `gallery`: url, feed_rss, feed_atom, model_count, last_updated
    - `models[]`: name, title, url, stl, tags, license, updated_at, links
    - Ordner `gallery/.well-known/` wird automatisch angelegt

- [ ] **Optionaler Aggregator-Ping in `action.yml`**
    - Neuer Input `aggregator-url` (optional, default leer)
    - Nach Gallery-Build: HTTP POST an `aggregator-url` mit Payload:
      `{ "discovery_url": "<base_url>/.well-known/cad-gallery.json", "repo": "<owner/repo>", "event": "push" }`
    - Ping nur wenn `aggregator-url` gesetzt ist

- [ ] **JSON Schema fuer `cad-gallery.json`** (`schemas/discovery.schema.json`)

## Projektstruktur

```
freecad-files/          # FreeCAD .FCStd Quelldateien (flach, keine Unterordner)
metadata/               # Metadaten-YAMLs (Name muss mit FCStd-Dateiname matchen)
  images/               # Zusaetzliche Bilder pro Modell
    {modellname}/
schemas/                # JSON Schemas fuer Validierung
  cad-gallery.schema.json
  maker.schema.json
  meta.schema.json
templates/              # Jinja2 HTML Templates
  gallery.html          # Gallery-Uebersicht
  detail.html           # Einzelansicht mit 3D-Viewer
  about.html            # Maker-Profilseite
  rss.xml
  atom.xml
scripts/                # Build-Scripts
  export.py             # FreeCAD -> STL/STEP Export
  build_gallery.py      # HTML Gallery generieren
  validate.py           # YAML gegen Schemas validieren
cad-gallery.yaml        # Konfiguration (Pfade, Gallery-Titel)
maker.yaml              # Maker-Profil (optional)
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

`cad-gallery.yaml` steuert alle Pfade und den Gallery-Titel:

```yaml
# yaml-language-server: $schema=...schemas/cad-gallery.schema.json
title: "Meine 3D-Modelle"   # optional, Default: "CAD Gallery"
freecad_dir: "freecad-files"
metadata_dir: "metadata"
output_dir: "gallery"
exports_dir: "exports"
```

`maker.yaml` definiert das Maker-Profil (optional):

```yaml
# yaml-language-server: $schema=...schemas/maker.schema.json
name: "Username"
bio: "Kurzbeschreibung"
links:
  github: "https://github.com/..."
  makerworld: "https://makerworld.com/..."
  thingiverse: "https://www.thingiverse.com/..."
  printables: "https://www.printables.com/..."
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
