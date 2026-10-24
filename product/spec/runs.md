# Runs

- **one-config:** A run is one YAML config: the market, each agent's model, prompt and temperature, and the seeds to play.
- **overrides:** Any config value can be changed from the command line without editing the file.
- **run-directory:** Every seed played writes its own directory holding the resolved config, the turn log and the summary.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `one-config` | not yet | — |
| `overrides` | not yet | — |
| `run-directory` | not yet | — |
