.PHONY: help
help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: ensure-scripts-exec
ensure-scripts-exec: ## Make scripts executable
	chmod +x scripts/*

.PHONY: setup
setup: ensure-scripts-exec ## Setup development environment (installs uv and syncs dependencies)
	./scripts/setup_uv.sh

.PHONY: test
test: ## Run tests with pytest
	uv run pytest tests/ -v

.PHONY: lint
lint: ## Run pre-commit hooks on all files
	uv run pre-commit run --all-files

.PHONY: generate-protos
generate-protos: ensure-scripts-exec ## Download proto files and generate Python code
	./scripts/generate_protos.sh

.PHONY: clean
clean: ## Clean generated files and caches
	rm -rf tmp/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/
