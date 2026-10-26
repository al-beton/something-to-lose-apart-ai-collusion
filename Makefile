# Implements: reproducibility/reported-numbers-checked, tooling/one-command-each, tooling/locked-dependencies, ci/end-to-end, reports/paper-figures, reports/paper-main-figures, reports/paper-project-image, reports/paper-source
.PHONY: install lint test spec-check e2e paper-figures reproduce paper-tools paper-html paper-tex paper-pdf paper-watch paper-build-dir
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
	uv run python reports/paper/project_image.py
reproduce:  # every committed number recomputed, offline; fails on a mismatch
	uv run python reports/reproduce.py

# The paper: write paper/paper.md, build to paper/build/ (gitignored).
PAPER_BUILD ?= paper/build
PANDOC = pandoc paper/paper.md --from markdown --resource-path=paper --number-sections --toc --toc-depth=2
paper-tools:
	@command -v pandoc >/dev/null || { echo "pandoc is missing: brew install pandoc (or see pandoc.org/installing)"; exit 1; }
paper-build-dir: paper-tools
	@mkdir -p $(PAPER_BUILD)/figures
	@cp reports/paper/figures/*.png $(PAPER_BUILD)/figures/
paper-html: paper-build-dir  # fast, for writing: open paper/build/paper.html
	@cp paper/style.css $(PAPER_BUILD)/
	$(PANDOC) --standalone --template paper/apart.html --css style.css --math-method=mathjax --citeproc -o $(PAPER_BUILD)/paper.html
paper-tex: paper-build-dir  # the .tex, with references.bib and figures/ beside it, ready for Overleaf
	@cp paper/references.bib $(PAPER_BUILD)/
	$(PANDOC) --template paper/apart.latex --natbib -o $(PAPER_BUILD)/paper.tex
paper-pdf: paper-tex
	@command -v tectonic >/dev/null || { echo "tectonic is missing: brew install tectonic (or see tectonic-typesetting.github.io)"; exit 1; }
	cd $(PAPER_BUILD) && tectonic --keep-logs paper.tex
PAPER_SOURCES = paper/paper.md paper/references.bib paper/style.css paper/apart.html
paper-watch: paper-html  # rebuild the HTML on every save (needs fswatch or entr); watches sources only, never the build
	@if command -v fswatch >/dev/null; then fswatch -o $(PAPER_SOURCES) | while read -r _; do $(MAKE) -s paper-html; done; \
	elif command -v entr >/dev/null; then ls $(PAPER_SOURCES) | entr $(MAKE) -s paper-html; \
	else echo "paper-watch needs fswatch or entr: brew install fswatch"; exit 1; fi
