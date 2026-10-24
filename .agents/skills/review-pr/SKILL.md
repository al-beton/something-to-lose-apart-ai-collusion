---
name: review-pr
description: Review a collusion-lab pull request, spec first, then tests, then how it's built, with inline findings. Use when asked to review any pull request in this repository.
---

<!-- Implements: agent-setup/shared-skills, agent-setup/skills-hold-the-process, ci/checks-over-prose, commits/deliberate-messages, commits/small-sane-steps, research/hypothesis-first, research/honest-limits, research/results-from-logs, research/every-run-committed, review/follows-the-rules, review/inline-findings, review/spec-first, safety/justified-dependencies, safety/no-secrets, specs-and-docs/docs-next-to-code, specs-and-docs/no-history, workflow/issue-scope, workflow/test-first -->

# Review a pull request

1. **Read the issues** in the closing block.
2. **Read in this order, stopping at the first problem:**
   1. **Spec:** is each new or changed statement good? It says what we want, not how; it's one short, plain sentence with a readable name; it contradicts nothing; it sits in the right area. A change in behaviour with no spec change, where the spec doesn't already cover it, is a finding.
   2. **Tests:** do the tests listed in the spec's "Where this is enforced" table prove the statements? Were they committed before the code that makes them pass?
   3. **How it's built:** does the code do what the statements say, in a reasonable and readable way? Do comments and docstrings explain what isn't obvious?
   4. **Research changes** (configs, prompts, analysis, write-ups): the question, arms and metrics are stated before the run; every reported number traces to a committed run's logs; every experiment run behind the change is committed under `runs/<experiment>/`; the limits are said plainly.
3. **Also check:**
   - no pull request or issue numbers, and no history, in code, specs or tests;
   - no API keys or other secrets in code, configs, commits, logs or test output;
   - the pull request covers only its issues;
   - commits are small and deliberately worded;
   - new dependencies are justified in the notes.

   Leave anything `pr-gate`, `spec-check`, lint or tests already check to CI.
4. **Report each finding inline,** on the lines it concerns. General remarks are only for the pull request as a whole (scope, title, description). Say what's wrong and what would fix it.
5. **If a rule you check by hand could be checked by CI**, propose it as an issue.
6. **Merge only through `merge-pr`.**
