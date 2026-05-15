.PHONY: help build serve validate clean

DOCKER_IMAGE ?= ghcr.io/schmiddim/freecad-action:latest

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Full build: export models via Docker + build gallery
	DOCKER_IMAGE=$(DOCKER_IMAGE) scripts/build.sh build

serve: build ## Build and serve locally on http://localhost:8000
	@echo "Serving gallery at http://localhost:8000"
	python3 -m http.server 8000 --directory gallery

validate: ## Validate metadata and profile YAML against JSON schemas
	python3 -m pip install --quiet jsonschema pyyaml
	python3 scripts/validate.py

clean: ## Remove generated files
	rm -rf gallery/ exports/
