# Workflow

- **issue-first:** Every piece of work starts from a GitHub issue that is well specced.
- **issue-scope:** A pull request handles one issue, or a parent issue together with its children.
- **test-first:** The tests that prove a statement are written, and seen failing, before the code that makes them pass.
- **blocked-means-ask:** When an agent is blocked or the spec is unclear, it asks on the issue instead of guessing.
- **draft-early:** Pull requests are opened early as drafts and marked ready once the code is done and passes locally; marking one ready runs CI, since drafts aren't checked.
- **al-only:** Only Al deals with accounts, API keys and spending.
- **prototype-pace:** collusion-lab is a prototype racing a hackathon deadline, so each issue aims for the smallest change that works and can be shared, and review stops once only edge cases remain.
- **one-routine:** An issue goes from start to merged through one routine that chains every step and says what to do when a step fails.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `issue-first` | `.agents/skills/build-issue/SKILL.md` | — |
| `issue-scope` | `.agents/skills/build-issue/SKILL.md`, `.agents/skills/review-pr/SKILL.md` | — |
| `test-first` | `.agents/skills/build-issue/SKILL.md`, `.agents/skills/review-pr/SKILL.md` | — |
| `blocked-means-ask` | `.agents/skills/build-issue/SKILL.md` | — |
| `draft-early` | `.agents/skills/build-issue/SKILL.md`, `.agents/skills/open-pr/SKILL.md` | — |
| `al-only` | `.agents/skills/build-issue/SKILL.md`, `AGENTS.md` | — |
| `prototype-pace` | `.agents/skills/deliver-issue/SKILL.md`, `AGENTS.md`, `.agents/skills/address-review/SKILL.md` | — |
| `one-routine` | `.agents/skills/deliver-issue/SKILL.md`, `.github/scripts/deliver.py`, `AGENTS.md` | — |
