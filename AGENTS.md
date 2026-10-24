<!-- Implements: agent-setup/entry-point, review/spec-first, safety/no-secrets, workflow/al-only -->
# collusion-lab: agent guide

collusion-lab is a small, quickly iterable environment for studying collusion between LLM agents in simulated markets, built for the Apart AI Collusion Research Sprint. A run is a config: the market, each agent's model, prompt and temperature, and a seed. Any run can be replayed exactly, and a sweep is one command.

## Where things are

- **Spec (intent, read first):** `product/spec/` (the lab), `experiments/spec/` (what we're finding out with it) and `contributing/spec/` (how we build it). One file per area. Each ends with "Where this is enforced", which says which files enforce each statement and which tests prove it.
- **Code:** `src/collusion_lab/`, tests in `tests/`, CI in `.github/`. Prompts in `prompts/` are sent to models verbatim, so they carry no comments; their spec rows trace them. Every file names the statements it implements on an `Implements:` line (files that can't hold comments, such as JSON, lockfiles and symlinks, are traced by their table row). Docs are the comments and docstrings next to the code.
- **How to do each step:** the skills in `.agents/skills/` (also linked as `.claude/skills/`): `build-issue`, `write-spec-change`, `trace-spec`, `open-pr`, `review-pr`, `address-review`, `merge-pr`.
- **Work** is tracked as GitHub issues on this repository.

Al handles accounts, API keys and spending. Agents never put keys in code, configs, logs or commits.

## Commands

```sh
make install      # uv dependencies
make lint         # ruff lint and format check
make test         # every test
make spec-check   # spec ↔ code ↔ tests traceability (fails CI if broken)
```

## The loop

Every issue goes **spec → failing test → code → trace → draft PR**, one small commit at a time (`build-issue`).

## Code review rules

Follow the `review-pr` skill. In short:
1. **Start with the spec.** Is each new or changed statement in `product/spec/` or `contributing/spec/` good? A behaviour change with no spec change is a finding.
2. **Then the code:** does it do what the statements say, reasonably? Its `Implements:` lines and the spec's "Where this is enforced" table must agree.
3. **Then the tests listed for each changed statement.**
4. **Never:** pull request or issue numbers in code, specs or tests; secrets anywhere.

Put each finding inline on the lines it concerns.
