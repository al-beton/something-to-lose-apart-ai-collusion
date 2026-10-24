# Tooling

- **one-command-each:** Installing, linting, testing and checking the spec are each one command.
- **locked-dependencies:** Dependencies are locked, so every machine installs the same versions.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `one-command-each` | `Makefile`, `README.md`, `pyproject.toml` | — |
| `locked-dependencies` | `uv.lock`, `.python-version`, `Makefile` | — |
