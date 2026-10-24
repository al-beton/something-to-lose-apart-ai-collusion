---
name: trace-spec
description: Connect collusion-lab spec statements to the code that enforces them and the tests that prove them. Use after building anything that implements, changes or removes a spec statement, or when spec-check warns.
---

<!-- Implements: agent-setup/shared-skills, agent-setup/skills-hold-the-process -->

# Trace the spec

Every statement says where it's enforced and how it's tested, and every file it names points back. `make spec-check` checks all of it.

1. **Fill the statement's row** in its spec file's `## Where this is enforced` table:
   - *Enforced by:* the files (`` `path` `` or a `` `glob/**` ``), and/or `reviewer`, and/or a setting such as `GitHub (…)`. Use `not yet` only while it's unbuilt.
   - *Tested by:* the names of the tests that prove it (`` `test_seeded_runs_replay_exactly` ``), or `—`.
2. **Point back from each file** with an `Implements:` line listing `area/statement` names, in the file's comment syntax:
   - Python, YAML, TOML, Makefile: `# Implements: runs/one-config, runs/overrides`
   - Markdown: `<!-- Implements: … -->`, after any front matter.

   Files that can't hold comments (JSON, lockfiles, symlinks) are homed by their table row alone, and so are prompts in `prompts/`: models read them verbatim, so they never carry an `Implements:` line.
3. **Every source file needs a home:** an `Implements:` line, or a row naming it. Tests name the statements they prove, too.
4. **Docs sit next to the code:** a module docstring or a comment explains how it works and why, where the code doesn't make it obvious. There are no separate docs folders.
5. **No history:** no pull request or issue numbers, and no "changed in…", in code, specs or tests. They describe the current state.
6. Run `make spec-check`. It fails on anything broken. Only `not yet` statements (deliberately left to a later issue, named in the pull request notes) and long spec files are allowed as warnings.
