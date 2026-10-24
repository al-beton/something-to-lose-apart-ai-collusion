# CI

- **one-gate:** A single required check gates every merge.
- **checks-on-every-pr:** Every pull request is checked, whatever branch it's based on, so stacked pull requests get the same checks as ones into main.
- **checks-over-prose:** Anything that can be checked automatically ends up checked by CI rather than left to the reviewer.
- **simple-code:** Code stays simple enough that the linter never calls it too complex.
- **ci-runs-everything:** CI runs the linter, every test and the spec check before anything merges.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `one-gate` | `.github/workflows/blocking-checks.yml` | — |
| `checks-on-every-pr` | `.github/workflows/blocking-checks.yml` | — |
| `checks-over-prose` | `.agents/skills/review-pr/SKILL.md` | — |
| `simple-code` | `pyproject.toml` | — |
| `ci-runs-everything` | `.github/workflows/ci.yml` | — |
