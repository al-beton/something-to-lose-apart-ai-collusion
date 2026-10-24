# CI

- **one-gate:** A single required check gates every merge.
- **checks-on-every-pr:** Every pull request is checked, whatever branch it's based on, so stacked pull requests get the same checks as ones into main.
- **checks-over-prose:** Anything that can be checked automatically ends up checked by CI rather than left to the reviewer.
- **simple-code:** Code stays simple enough that the linter never calls it too complex.
- **ci-runs-everything:** CI runs the linter, every test and the spec check before anything merges.
- **end-to-end:** Every pull request proves the whole path works: free scripted agents play a small sweep with talk through the real `lab` commands, then `lab summary` and `lab report` turn it into a table and a page whose numbers, sections and highlights are checked; `make e2e` runs the same test offline, for free, in seconds.
- **ci-minutes:** CI costs about one billed minute per run: every check runs as a step of one job, since GitHub bills each job as at least a minute, a newer run for the same pull request cancels the one in progress, and draft pull requests are not checked until they are marked ready (the repository is private, so minutes count against Al's quota, about 2,000 a month free).
- **report-comment:** Every pull request carries one comment, edited in place on each push, with the first screen of a report on one free scripted game and a link to the full report; the game or report failing fails the checks, while a comment that can't be posted doesn't.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `one-gate` | `.github/workflows/blocking-checks.yml` | — |
| `checks-on-every-pr` | `.github/workflows/blocking-checks.yml` | — |
| `checks-over-prose` | `.agents/skills/review-pr/SKILL.md` | — |
| `simple-code` | `pyproject.toml` | — |
| `end-to-end` | `tests/test_e2e.py`, `.github/workflows/blocking-checks.yml`, `Makefile` | `test_end_to_end_plays_every_arm_and_seed_into_its_own_folder`, `test_end_to_end_summary_numbers_make_sense`, `test_end_to_end_report_has_every_section_and_highlights` |
| `ci-runs-everything` | `.github/workflows/blocking-checks.yml` | `test_ci_minutes_one_job_runs_every_check` |
| `ci-minutes` | `.github/workflows/blocking-checks.yml`, `.agents/skills/open-pr/SKILL.md`, `.agents/skills/deliver-issue/SKILL.md` | `test_ci_minutes_one_job_named_like_the_gate`, `test_ci_minutes_one_job_runs_every_check`, `test_ci_minutes_newer_runs_cancel_older_ones_and_drafts_wait` |
| `report-comment` | `.github/workflows/blocking-checks.yml`, `.github/scripts/report_comment.py`, `configs/pr-game.yaml` | `test_report_comment_shows_the_first_screen_commit_and_link`, `test_report_comment_is_one_comment_edited_in_place`, `test_report_comment_failing_to_post_never_fails_the_checks`, `test_markdown_first_screen_of_the_pull_request_game` |
