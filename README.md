<!-- Implements: tooling/one-command-each -->
# collusion-lab

A small, quickly iterable environment for studying collusion between LLM agents in simulated markets, built for the [Apart AI Collusion Research Sprint](https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25).

## Start

Needs [uv](https://docs.astral.sh/uv/).

```sh
make install      # dependencies, locked
make lint
make test
make spec-check   # spec ↔ code ↔ tests traceability
```

## How we work

Spec first, then a failing test, then code. Start at [AGENTS.md](AGENTS.md).
