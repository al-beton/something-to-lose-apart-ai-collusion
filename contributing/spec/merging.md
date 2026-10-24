# Merging

- **squash-only:** Pull requests are squash-merged, so noisy histories never reach main.
- **merge-is-authorised:** Only someone the merge-pr skill authorises may press merge.
- **merge-when-clean:** A pull request merges only when checks are green, every finding is resolved and the closing block is right.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `squash-only` | `.agents/skills/merge-pr/SKILL.md` | — |
| `merge-is-authorised` | `.agents/skills/merge-pr/SKILL.md` | — |
| `merge-when-clean` | `.agents/skills/merge-pr/SKILL.md` | — |
