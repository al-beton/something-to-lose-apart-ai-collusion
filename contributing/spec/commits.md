# Commits

- **small-sane-steps:** Commits are small steps that each leave the codebase in a sane state, or at least form a logical chunk.
- **deliberate-messages:** Commit messages are deliberate and say what changed.
- **commit-refs-issue:** Each commit references the issue it moves forward.
- **grooming-optional:** Tidying a pull request's commits is optional and never happens while a review is in progress.
- **named-paths:** Commits stage only the paths they name, and run output is committed only when it is asked for by name.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `small-sane-steps` | `.agents/skills/build-issue/SKILL.md`, `.agents/skills/review-pr/SKILL.md` | — |
| `deliberate-messages` | `.agents/skills/build-issue/SKILL.md`, `.agents/skills/review-pr/SKILL.md` | — |
| `commit-refs-issue` | `.agents/skills/build-issue/SKILL.md` | — |
| `grooming-optional` | `.agents/skills/address-review/SKILL.md`, `.agents/skills/merge-pr/SKILL.md` | — |
| `named-paths` | `.agents/skills/deliver-issue/SKILL.md`, `.github/scripts/deliver.py` | `test_named_paths_refuse_everything_and_run_output` |
