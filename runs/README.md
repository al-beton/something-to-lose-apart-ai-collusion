# Runs

Every committed game, one folder per experiment, then one per run and seed. Each seed folder holds exactly what the lab wrote:

- **`config.yaml`:** the resolved config it played.
- **`manifest.json`:** the commit, prompt hashes, models and providers that answered, and cost.
- **`timings.jsonl`:** each call's model version, host, tokens, cost and whether the cache answered it.
- **`summary.json`:** prices, gains, agreements and audit outcomes.
- **`turns.compact.jsonl`:** every turn's moves and messages (the full prompts and replies rebuild from `archive/`).

`index.jsonl` has one line per command that wrote here. `uv run lab summary runs/<folder>` and `uv run lab report runs/<folder>` read any folder. `runs/scratch/` is for your own runs and is never committed.
