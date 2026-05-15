.PHONY: help build serve validate clean docker-build export gallery install

PYTHON := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null)
DOCKER_IMAGE := cad-gallery-freecad
GALLERY_CONFIG := gallery.yaml

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	$(PYTHON) -m pip install -e ".[dev]"

validate: ## Validate metadata and profile YAML against JSON schemas
	$(PYTHON) scripts/validate.py

docker-build: ## Build the FreeCAD Docker image
	docker build -t $(DOCKER_IMAGE) .

export: docker-build ## Export STL + STEP from FCStd files (via Docker)
	docker run --rm \
		-v "$$(pwd):/workspace" \
		$(DOCKER_IMAGE) \
		scripts/export.py

gallery: ## Build the HTML gallery (no Docker needed)
	$(PYTHON) scripts/build_gallery.py

build: export gallery ## Full build: export models + build gallery

serve: gallery ## Build gallery and serve locally on http://localhost:8000
	@echo "Serving gallery at http://localhost:8000"
	$(PYTHON) -m http.server 8000 --directory gallery

clean: ## Remove generated files
	rm -rf gallery/ exports/
