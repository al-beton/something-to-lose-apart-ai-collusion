---
name: open-pr
description: Open or update a collusion-lab pull request with the right title, template and closing block, then request review. Use whenever creating a pull request or marking one ready.
---

<!-- Implements: agent-setup/shared-skills, agent-setup/skills-hold-the-process, pull-requests/closing-block, pull-requests/template, pull-requests/title-shows-type-and-issues, review/every-reviewer-counts, safety/justified-dependencies, workflow/draft-early -->

# Open a pull request

1. **Title:** `<type>(<area>): <summary> (<issues>)`. `pr-gate` checks it and re-runs when you edit it.
   - Type: `feat` (new behaviour the spec gains), `fix` (the code doesn't do what the spec says), or `improve` (everything else: deeper spec, refactors, CI, dependency updates).
   - Area: the spec file the change mainly belongs to (`runs`, `pull-requests`, …). It must exist.
   - Issues: one or more, separated by ", ": `feat(runs): run a game from one config (#2, #3)`.
2. **Description:** fill in `.github/pull_request_template.md`: issues, spec changes (quoted, first, because review starts there), how it's built, tests, notes. Sections that don't apply say "None".
3. **Closing block:** one line per issue.
   - `Closes`, `Fixes` or `Resolves` for issues this pull request finishes (GitHub closes them on merge);
   - `Part of`, `Refs` or `Towards` for issues it only moves forward.

   Every issue in the title must appear here.
4. **New dependencies:** say why in the notes, and commit the updated `uv.lock`.
5. **Draft, then ready:** open it as a draft (`gh pr create --draft`). Mark it ready when `blocking-checks` is green.
6. **Request review** when marking it ready. Automatic reviewers' findings count like anyone else's.
