# CI

- **one-gate:** A single required check gates every merge.
- **checks-on-every-pr:** Every pull request is checked, whatever branch it's based on, so stacked pull requests get the same checks as ones into main.
- **checks-over-prose:** Anything that can be checked automatically ends up checked by CI rather than left to the reviewer.
- **simple-code:** Code stays simple enough that the linter never calls it too complex.
- **ci-runs-everything:** CI runs the linter, every test and the spec check before anything merges.
- **docs-fast:** A pull request that changes only the paper's text (`paper/*.md`, `paper/*.bib`), the submission pack (`submission/`) or READMEs skips the linter, the full test suite and the digest, since none of those files can break code or a checked number; it still gets the title check, the spec check and the tests that read the paper, the figures' paper lines and the READMEs. Code, prompts, specs, findings notes and the paper's build always run everything.
- **end-to-end:** Every pull request proves the whole path works: free scripted agents play a small sweep with talk through the real `lab` commands, then `lab summary` and `lab report` turn it into a table and a page whose numbers, sections and highlights are checked; `make e2e` runs the same test offline, for free, in seconds.
- **ci-minutes:** The gate is quick: every check that gates a merge is a step of the one `blocking-checks` job, the tests run in parallel (one worker per core) and dependencies are cached between runs; the free demo game, its report and comment, and the digest run in a second job, `pr-report`, beside the gate, which never waits for it. A newer run for the same pull request cancels the one in progress, and draft pull requests are not checked until they are marked ready.
- **report-comment:** Every pull request carries one comment, edited in place on each push, with the first screen of a report on one free scripted game and a link to the full report; the game or report failing fails the `pr-report` job, which isn't the gate, while a comment that can't be posted doesn't fail it.
- **paper-preview:** A push that touches the paper, its figures or its build, drafts included, builds the paper to HTML, LaTeX and PDF, publishes them to GitHub Pages under the pull request's number (or `main/`), and keeps one comment on the pull request, edited in place, linking the HTML and the PDF, with the page count and the build's abstract and page-cap warnings. It is its own workflow, not a step of the gate, so it never blocks a merge; the repository is public, so its minutes are free.
- **no-model-calls:** CI never calls a model: only mock agents and committed data; no API keys are stored as secrets.
- **results-digest:** A pull request that changes committed runs, reports or the report code also gets, in its one comment, the results of the registered experiments it touches: per experiment, folded away, the `lab analyse` table with a strip of every game's gain, a Mermaid chart of each cell's mean gain and up to three of its indexed moments, all inline and cut to fit a comment; every push to main updates one "Results digest" issue in place with every registered experiment the same way.
- **numbers-checked:** A number a findings note marks (`<!-- check: CELL | COLUMN = VALUE -->`) is recomputed from the committed runs whenever a pull request changes runs or reports, and a mismatch fails the gate.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `one-gate` | `.github/workflows/blocking-checks.yml` | — |
| `checks-on-every-pr` | `.github/workflows/blocking-checks.yml` | — |
| `checks-over-prose` | `.agents/skills/review-pr/SKILL.md` | — |
| `simple-code` | `pyproject.toml` | — |
| `end-to-end` | `tests/test_e2e.py`, `.github/workflows/blocking-checks.yml`, `Makefile` | `test_end_to_end_plays_every_arm_and_seed_into_its_own_folder`, `test_end_to_end_summary_numbers_make_sense`, `test_end_to_end_report_has_every_section_and_highlights` |
| `docs-fast` | `.github/workflows/blocking-checks.yml`, `.github/scripts/docs_only.py` | `test_docs_fast_only_text_files_skip_the_slow_checks` |
| `ci-runs-everything` | `.github/workflows/blocking-checks.yml`, `Makefile` | `test_ci_minutes_the_gate_runs_every_check` |
| `ci-minutes` | `.github/workflows/blocking-checks.yml`, `Makefile`, `pyproject.toml`, `uv.lock`, `.agents/skills/open-pr/SKILL.md`, `.agents/skills/deliver-issue/SKILL.md` | `test_ci_minutes_the_gate_is_one_job_and_the_report_runs_beside_it`, `test_ci_minutes_tests_run_in_parallel_with_cached_dependencies`, `test_ci_minutes_the_gate_runs_every_check`, `test_ci_minutes_newer_runs_cancel_older_ones_and_drafts_wait` |
| `report-comment` | `.github/workflows/blocking-checks.yml`, `.github/scripts/report_comment.py`, `configs/pr-game.yaml` | `test_report_comment_shows_the_first_screen_commit_and_link`, `test_report_comment_is_one_comment_edited_in_place`, `test_report_comment_failing_to_post_never_fails_the_checks`, `test_markdown_first_screen_of_the_pull_request_game` |
| `paper-preview` | `.github/workflows/paper-preview.yml` | `test_paper_preview_builds_publishes_and_comments` |
| `no-model-calls` | `.github/workflows/blocking-checks.yml`, `configs/pr-game.yaml` | `test_no_model_calls_in_any_config_ci_plays`, `test_no_model_calls_no_secret_but_the_github_token` |
| `results-digest` | `.github/workflows/blocking-checks.yml`, `.github/scripts/report_comment.py`, `.github/scripts/digest_issue.py`, `src/collusion_lab/digest.py` | `test_results_digest_joins_the_report_comment`, `test_results_digest_issue_updated_in_place`, `test_results_digest_fits_a_comment` |
| `numbers-checked` | `.github/workflows/blocking-checks.yml`, `src/collusion_lab/digest.py` | `test_numbers_checked_against_the_runs` |
