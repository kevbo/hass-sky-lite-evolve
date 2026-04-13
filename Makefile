SHELL := /bin/bash
.DEFAULT_GOAL := help

PYTHON_VERSION := $(shell cat .python-version)
VENV := .venv

# Use system python3 if ruff/pytest are available (devcontainer),
# otherwise fall back to .venv (local mac/linux).
RUFF := $(shell command -v ruff 2>/dev/null || echo $(VENV)/bin/ruff)
PYTEST := $(shell command -v pytest 2>/dev/null || echo $(VENV)/bin/pytest)
NEED_VENV := $(if $(shell command -v ruff 2>/dev/null),,yes)

# ──────────────────────────────────────────────
# Python / pyenv (only needed outside devcontainer)
# ──────────────────────────────────────────────

.PHONY: check-pyenv
check-pyenv:
	@command -v pyenv >/dev/null 2>&1 || { \
		echo "pyenv not found. Install it: https://github.com/pyenv/pyenv#installation"; \
		exit 1; \
	}

.PHONY: install-python
install-python: check-pyenv
	@pyenv versions --bare | grep -q "^$(PYTHON_VERSION)$$" || { \
		echo "Installing Python $(PYTHON_VERSION) via pyenv..."; \
		pyenv install $(PYTHON_VERSION); \
	}
	@echo "Python $(PYTHON_VERSION) available"

$(VENV)/bin/activate: install-python requirements.txt
	@test -d $(VENV) || python -m venv $(VENV)
	@$(VENV)/bin/pip install --quiet --upgrade pip
	@$(VENV)/bin/pip install --quiet -r requirements.txt
	@$(VENV)/bin/pip install --quiet pytest pytest-homeassistant-custom-component
	@touch $(VENV)/bin/activate

.PHONY: venv
venv: $(VENV)/bin/activate ## Create local virtualenv (not needed in devcontainer)

# ──────────────────────────────────────────────
# Lint / check
# ──────────────────────────────────────────────

.PHONY: lint
lint: $(if $(NEED_VENV),venv) ## Run ruff linter
	@$(RUFF) check .

.PHONY: format
format: $(if $(NEED_VENV),venv) ## Run ruff formatter
	@$(RUFF) format .

.PHONY: format-check
format-check: $(if $(NEED_VENV),venv) ## Check formatting without modifying
	@$(RUFF) format --check .

.PHONY: check
check: lint format-check ## Run all checks (lint + format)

# ──────────────────────────────────────────────
# Test
# ──────────────────────────────────────────────

.PHONY: test
test: $(if $(NEED_VENV),venv) ## Run tests
	@$(PYTEST) tests/ -v

.PHONY: test-cov
test-cov: $(if $(NEED_VENV),venv) ## Run tests with coverage
	@$(PYTEST) tests/ -v --cov=custom_components.sky_lite_evolve --cov-report=term-missing

# ──────────────────────────────────────────────
# Development (devcontainer)
# ──────────────────────────────────────────────

.PHONY: setup
setup: ## Install deps (used by devcontainer postCreateCommand)
	@scripts/setup

.PHONY: develop
develop: ## Run HA with integration loaded
	@scripts/develop

.PHONY: clean
clean: ## Remove local venv
	@rm -rf $(VENV)
	@echo "Cleaned up."

# ──────────────────────────────────────────────
# Help
# ──────────────────────────────────────────────

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'
