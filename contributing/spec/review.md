# Review

- **reviewed-before-merge:** Every pull request is reviewed before it merges.
- **spec-first:** Review starts with the spec: first check that the spec change is good, then that it is implemented correctly and reasonably.
- **follows-the-rules:** The reviewer checks that the change follows the contributing rules.
- **inline-findings:** Review findings go inline, on the lines they are about.
- **resolve-with-commit:** Every finding is addressed and resolved with a reply: naming the commit that fixed it, or explaining why nothing changed.
- **every-reviewer-counts:** Findings from automatic reviewers count the same as anyone else's.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `reviewed-before-merge` | `.agents/skills/merge-pr/SKILL.md` | — |
| `spec-first` | `.agents/skills/review-pr/SKILL.md`, `AGENTS.md` | — |
| `follows-the-rules` | `.agents/skills/review-pr/SKILL.md` | — |
| `inline-findings` | `.agents/skills/review-pr/SKILL.md` | — |
| `resolve-with-commit` | `.agents/skills/address-review/SKILL.md` | — |
| `every-reviewer-counts` | `.agents/skills/address-review/SKILL.md`, `.agents/skills/open-pr/SKILL.md` | — |
