# CI

- **one-gate:** A single required check gates every merge.
- **checks-on-every-pr:** Every pull request is checked, whatever branch it's based on, so stacked pull requests get the same checks as ones into main.
- **checks-over-prose:** Anything that can be checked automatically ends up checked by CI rather than left to the reviewer.
- **simple-code:** Code stays simple enough that the linter never calls it too complex.
- **ci-runs-everything:** CI runs the linter, every test and the spec check before anything merges.
- **smoke-evidence:** Every pull request shows the summary table of a free mock run as one comment, kept up to date on each push, and its checks fail if that run fails.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `one-gate` | `.github/workflows/blocking-checks.yml` | — |
| `checks-on-every-pr` | `.github/workflows/blocking-checks.yml` | — |
| `checks-over-prose` | `.agents/skills/review-pr/SKILL.md` | — |
| `simple-code` | `pyproject.toml` | — |
| `smoke-evidence` | `.github/workflows/blocking-checks.yml`, `.github/scripts/smoke_comment.py`, `Makefile` | `test_smoke_evidence_comment_shows_the_table_and_commit`, `test_smoke_evidence_is_one_comment_edited_in_place` |
| `ci-runs-everything` | `.github/workflows/ci.yml` | — |
