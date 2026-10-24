# Implements: tooling/one-command-each, tooling/locked-dependencies
.PHONY: install lint test spec-check
install:
	uv sync --frozen
lint:
	uv run ruff check .
	uv run ruff format --check .
test:
	uv run pytest
spec-check:
	uv run python .github/scripts/spec_check.py
