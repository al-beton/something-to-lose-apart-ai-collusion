# Tooling

- **one-command-each:** Installing, linting, testing and checking the spec are each one command.
- **locked-dependencies:** Dependencies are locked, so every machine installs the same versions.
- **quick-start:** The README takes a newcomer from a fresh clone to a free mock run, its report and then a real model run in minutes, without asking anyone.
- **key-setup:** The README says where to get a model API key, how to cap its spending and that the sprint gives no model credits, and an example env file shows which variable to fill in.
- **how-tos:** The README says where to make each common change (a prompt, a model, a sweep, the market, a highlight rule, an experiment), naming the file and the spec area, and every file it names exists.
- **how-we-work:** The README gives people the working process in five lines and sends coding agents to `AGENTS.md`.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `one-command-each` | `Makefile`, `README.md`, `pyproject.toml` | — |
| `locked-dependencies` | `uv.lock`, `.python-version`, `Makefile` | — |
| `quick-start` | not yet | — |
| `key-setup` | not yet | — |
| `how-tos` | not yet | — |
| `how-we-work` | not yet | — |
