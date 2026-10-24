---
name: merge-pr
description: Merge a collusion-lab pull request when authorised and every merge condition holds. Use only when asked to merge, or when you reviewed the pull request and are authorised to merge it.
---

<!-- Implements: agent-setup/shared-skills, agent-setup/skills-hold-the-process, commits/grooming-optional, merging/merge-is-authorised, merging/merge-when-clean, merging/squash-only, review/reviewed-before-merge -->

# Merge a pull request

1. **Are you allowed to merge?**

   | Who | May merge when |
   |---|---|
   | Al | always |
   | Codex or Claude | Al has explicitly told it to merge that pull request |

   If you aren't allowed, stop and say so. Changing this table is a spec-level decision for Al.
2. **Check every condition, and stop at the first that fails:**
   1. someone other than the author has reviewed it;
   2. `blocking-checks` is green;
   3. every review conversation is resolved;
   4. the squash message contains the closing block, so GitHub closes every finished issue.
3. **Tidying commits is optional,** and only after the final review: `git commit --fixup`, `git rebase --autosquash`, `git push --force-with-lease`, then a comment saying what was reorganised.
4. **Squash-merge** (`gh pr merge --squash`). The squash title is the pull request title.
