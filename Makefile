# Implements: tooling/one-command-each, tooling/locked-dependencies, ci/end-to-end
.PHONY: install lint test spec-check e2e
install:
	uv sync --frozen
lint:
	uv run ruff check .
	uv run ruff format --check .
test:
	uv run pytest
spec-check:
	uv run python .github/scripts/spec_check.py
e2e:  # free scripted agents: run -> summary -> report, offline, in seconds
	uv run pytest tests/test_e2e.py
