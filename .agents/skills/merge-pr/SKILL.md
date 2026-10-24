---
name: merge-pr
description: Merge a collusion-lab pull request when authorised and every merge condition holds. Use when you reviewed a pull request you didn't author and it passed, or when Al asks you to merge.
---

<!-- Implements: agent-setup/shared-skills, agent-setup/skills-hold-the-process, commits/grooming-optional, merging/merge-is-authorised, merging/merge-when-clean, merging/squash-only, review/reviewed-before-merge, team/reviewers -->

# Merge a pull request

1. **Are you allowed to merge?**

   | Who | May merge when |
   |---|---|
   | Al | always |
   | A reviewer agent | it isn't the pull request's author, and its own review (`review-pr`) passed |
   | Anyone else, including the builder who opened it | never |

   If you aren't allowed, stop and say so. Changing this table is a spec-level decision for Al.
2. **Check every condition, and stop at the first that fails:**
   1. someone other than the author has reviewed it;
   2. `blocking-checks` is green;
   3. Codex has finished reviewing the latest commit (`python3 .github/scripts/deliver.py wait-review <pr>`);
   4. every review conversation is resolved;
   5. the squash message contains the closing block, so GitHub closes every finished issue.
3. **Tidying commits is optional,** and only after the final review: `git commit --fixup`, `git rebase --autosquash`, `git push --force-with-lease`, then a comment saying what was reorganised.
4. **Squash-merge** with `python3 .github/scripts/deliver.py merge <pr>`: it checks 2 to 5 again, squash-merges with the pull request title, deletes the branch and waits for `main` to go green.
5. **Tell the delivery lead** what merged, and move the issue's label off `in-review` (GitHub closes the issue).
