<!-- Implements: research/outputs-home -->
# Reports

Findings from experiments, one folder per experiment (`reports/<experiment>/`), named like its spec in `experiments/spec/`.

- **Notes** (`*.md`) are committed: what was run, what we found, with every number traced to a committed run's logs, and what it can't show.
- **Report pages** from `lab report runs/<folder> --out reports/<experiment>/<name>.html` are gitignored: they're rebuilt from the runs at any time, and shared as files.
