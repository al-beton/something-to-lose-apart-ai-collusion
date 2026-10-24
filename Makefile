# Implements: tooling/one-command-each, tooling/locked-dependencies, ci/smoke-evidence
.PHONY: install lint test spec-check smoke
install:
	uv sync --frozen
lint:
	uv run ruff check .
	uv run ruff format --check .
test:
	uv run pytest
spec-check:
	uv run python .github/scripts/spec_check.py
smoke:  # free mock agents only; the table lands in runs/smoke/summary.md
	rm -rf runs/smoke
	uv run lab run configs/smoke.yaml --out runs/smoke --cache off -y
	uv run lab summary runs/smoke > runs/smoke/summary.md
	cat runs/smoke/summary.md
