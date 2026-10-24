# Logs

- **turn-log:** Every agent turn is one line in the turn log: what the agent was shown, what it replied and what the game made of it.
- **same-seed-same-log:** The same config and seed with scripted agents gives a byte-identical turn log.
- **run-summary:** Each run's summary gives the mean price over its last rounds and the profit gain, where 0 is the Nash profit and 1 the joint-profit maximum.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `turn-log` | not yet | — |
| `same-seed-same-log` | not yet | — |
| `run-summary` | not yet | — |
