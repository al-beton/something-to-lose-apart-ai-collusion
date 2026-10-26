<!-- Implements: specs-and-docs/folder-guides -->
# Source

The lab, `collusion_lab`, run as `lab` on the command line (`cli.py`).

- **A game:** `market.py` (the markets), `agents.py` and `prompts.py` (what agents see and how replies are read), `runner.py` (rounds of talk and prices), `conditions/` (audits, free time, leniency, offers).
- **Models:** `backends.py` (any LiteLLM model, cached in `.cache/`), `config.py` (configs and model aliases).
- **Results:** `summary.py`, `analysis.py`, `report/` (the HTML report) and `charts.py`.
- **Replay:** `archive.py`, `forks.py`, `manifest.py`, `provenance.py`.

Each file's docstring says what it does and names the spec statements it implements.
