# Reproducibility

- **response-cache:** Every model reply is stored under everything that shaped it (model, address, messages, temperature, token limit, seed and attempt), so re-running a config and seed replays it exactly without calling the model again.
- **cache-modes:** A run can use the cache, refresh it or leave it out; a fresh sample comes from a new seed, never from clearing the cache.
- **manifest:** Every run records what produced it: the resolved config, a hash of each prompt file it used, the code version, package versions, the model versions that answered, and its calls, tokens, cache hits and cost.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `response-cache` | not yet | — |
| `cache-modes` | not yet | — |
| `manifest` | not yet | — |
