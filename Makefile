# Implements: reproducibility/reported-numbers-checked, tooling/one-command-each, tooling/locked-dependencies, ci/end-to-end, reports/paper-figures, reports/paper-main-figures
.PHONY: install lint test spec-check e2e paper-figures reproduce
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
paper-figures:  # the paper's figures and tables, offline, from committed runs
	uv run python reports/paper/build.py
	uv run python reports/paper/figures.py
	uv run python reports/paper/fig1_round.py
reproduce:  # every committed number recomputed, offline; fails on a mismatch
	uv run python reports/reproduce.py
