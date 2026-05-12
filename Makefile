.PHONY: help install dev test lint format clean install-skill uninstall-skill

PYTHON ?= python3
SKILL_NAME := lecture-video-to-doc
USER_SKILLS_DIR := $(HOME)/.claude/skills

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## pip install slidoc (production)
	$(PYTHON) -m pip install -e .

dev:  ## pip install with dev extras
	$(PYTHON) -m pip install -e ".[dev]"

test:  ## Run pytest
	$(PYTHON) -m pytest

lint:  ## Lint with ruff
	$(PYTHON) -m ruff check slidoc tests

format:  ## Format with ruff
	$(PYTHON) -m ruff format slidoc tests

clean:  ## Remove build artifacts
	rm -rf build dist *.egg-info .pytest_cache .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

install-skill:  ## Symlink the Claude Code skill into ~/.claude/skills
	mkdir -p $(USER_SKILLS_DIR)
	ln -sfn $(CURDIR)/.claude/skills/$(SKILL_NAME) $(USER_SKILLS_DIR)/$(SKILL_NAME)
	@echo "Installed: $(USER_SKILLS_DIR)/$(SKILL_NAME) → $(CURDIR)/.claude/skills/$(SKILL_NAME)"

uninstall-skill:  ## Remove the symlinked skill
	rm -f $(USER_SKILLS_DIR)/$(SKILL_NAME)
	@echo "Removed: $(USER_SKILLS_DIR)/$(SKILL_NAME)"
