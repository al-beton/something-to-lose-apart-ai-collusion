---
name: build-issue
description: Build a collusion-lab GitHub issue end to end, from issue to branch to spec to failing test to code to draft pull request. Use when starting work on any issue in this repository.
---

<!-- Implements: agent-setup/shared-skills, agent-setup/skills-hold-the-process, commits/commit-refs-issue, commits/deliberate-messages, commits/small-sane-steps, specs-and-docs/docs-next-to-code, workflow/al-only, workflow/blocked-means-ask, workflow/draft-early, workflow/issue-first, workflow/issue-scope, workflow/test-first -->

# Build an issue

1. **Start from a GitHub issue** on this repository (`gh issue view <n>`). It must be well specced:
   1. its title states the outcome in plain words;
   2. it says why, and which spec area it changes;
   3. it says its type (bug fix, improvement or new feature);
   4. it has one deliverable;
   5. its acceptance criteria are checkboxes, each checkable from the pull request;
   6. anything only Al can do is under "Al does";
   7. its order is set with "Blocked by #<n>" lines.

   If it isn't well specced, improve the issue or ask first. A pull request covers one issue, or one parent issue and its children; unrelated changes go in their own pull request.
2. **Branch** from the latest base: `<n>-<short-slug>` (for example `3-litellm-backend`).
3. **Spec first:** write the spec change (`write-spec-change`), commit it, push, and open a draft pull request straight away (`open-pr`).
4. **Test first:** write the tests that prove each new or changed statement, run them and watch them fail for the right reason, then commit them on their own ("Test that …").
5. **Build:** the smallest code that makes those tests pass, then connect code and tests to the spec (`trace-spec`). Docs are module docstrings and comments next to the code.
6. **Commit in small, sane steps.** The usual shape of a pull request is three or more commits: "Spec: …", "Test …", then the code. Each commit leaves the codebase working, or is a logical chunk of a bigger change.
   - Subject: imperative, at most 72 characters, says what changed.
   - Body: anything the diff doesn't show, ending with `Refs: #<n>`.
7. **Before marking ready:** `make lint`, `make test` and `make spec-check` pass.
8. **When blocked or unsure**, comment on the issue with the question and a recommended answer, and carry on with everything else.
9. **Only Al** creates accounts, handles API keys or decides spending. A run that calls a paid model prints how many calls it will make and waits for a yes. Write the exact steps for Al under "Al does" on the issue.
