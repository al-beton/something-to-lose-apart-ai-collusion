---
name: address-review
description: Address review findings on a collusion-lab pull request (from an automatic reviewer or a person) and resolve each one. Use when a pull request has unresolved review comments.
---

<!-- Implements: agent-setup/shared-skills, agent-setup/skills-hold-the-process, commits/grooming-optional, review/every-reviewer-counts, review/resolve-with-commit, review/bounded-rounds, workflow/prototype-pace -->

# Address review findings

1. **Judge every finding,** whoever wrote it: automatic reviewers and people count the same. Fix what's real: bugs, contradictions, places where the code doesn't do what the spec says. Decline the rest with a reason, such as hypothetical edge cases, speculative hardening or scope creep.
2. **Fix in new commits on top.** Don't rewrite history while a review is in progress.
3. **Answer in the finding's thread, then resolve it:**
   - fixed: name the commit ("Fixed in 1a2b3c4: …");
   - not changed: explain why.

   Findings with no thread (in a review summary) get one pull request comment covering them.
4. **Check again:** `blocking-checks` green. If the fixes change behaviour, ask for another review.
5. **Stop after three automatic review rounds,** or sooner when a round finds nothing real; decline what's left with a reason or open an issue for it. `python3 .github/scripts/deliver.py resolve THREAD REPLY` replies and resolves in one step.
