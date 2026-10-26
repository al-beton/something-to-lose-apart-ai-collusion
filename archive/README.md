<!-- Implements: specs-and-docs/folder-guides, reproducibility/cache-archive -->
# Archive

The model replies behind every committed run in `runs/`, so any game replays offline with no model called.

- **`<experiment>.jsonl.gz`:** the replies alone, compressed, one file per experiment (none over 20 MB).
- **`index.json`:** each run's file, and whether the archive reproduces it decision for decision.

`uv run lab archive replay runs/<experiment>/<run>/seed-0 --archive archive --out replayed` rebuilds a run's full log. How the archive is packed and what it can't pin is in [REPRODUCIBILITY.md](../REPRODUCIBILITY.md).
