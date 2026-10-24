# Merging

- **squash-only:** Pull requests are squash-merged, so noisy histories never reach main.
- **merge-is-authorised:** Al may always merge; a reviewer agent may merge a pull request it didn't author once its own review passed; nobody else may.
- **merge-when-clean:** A pull request merges only when checks are green, Codex has finished reviewing its latest commit, every finding is resolved and the closing block is right.
- **stacked-retarget:** Before a merged branch is deleted, every pull request based on it is moved to main, so none closes by accident.
- **main-stays-green:** After every merge, main's checks run again and must pass.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `squash-only` | `.agents/skills/merge-pr/SKILL.md` | — |
| `merge-is-authorised` | `.agents/skills/merge-pr/SKILL.md` | — |
| `merge-when-clean` | `.agents/skills/merge-pr/SKILL.md`, `.github/scripts/deliver.py` | `test_merge_when_clean_keeps_the_closing_block`, `test_merge_when_clean_refuses_red_checks_or_open_threads` |
| `stacked-retarget` | `.agents/skills/deliver-issue/SKILL.md`, `.github/scripts/deliver.py` | `test_stacked_retarget_happens_before_the_branch_is_deleted` |
| `main-stays-green` | `.agents/skills/deliver-issue/SKILL.md`, `.github/scripts/deliver.py` | `test_main_stays_green_reruns_checks_after_merging` |
