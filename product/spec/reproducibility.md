# Reproducibility

- **response-cache:** Every model reply is stored under everything that shaped it (model, address, messages, temperature, token limit, seed and attempt), so re-running a config and seed replays it exactly without calling the model again.
- **cache-modes:** A run can use the cache, refresh it or leave it out; a fresh sample comes from a new seed, never from clearing the cache.
- **manifest:** Every run records what produced it: the resolved config, a hash of each prompt file it used, the code version, package versions, the model versions that answered, and its calls, tokens, cache hits and cost.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `response-cache` | `src/collusion_lab/cache.py`, `src/collusion_lab/runner.py` | `test_response_cache_replays_a_run_exactly_without_calling`, `test_response_cache_misses_when_the_seed_changes` |
| `cache-modes` | `src/collusion_lab/cache.py`, `src/collusion_lab/cli.py` | `test_cache_modes_refresh_calls_again_and_stores_the_new_reply`, `test_cache_modes_off_neither_reads_nor_stores`, `test_cache_modes_mock_agents_skip_the_cache` |
| `manifest` | `src/collusion_lab/manifest.py`, `src/collusion_lab/runner.py` | `test_manifest_records_what_produced_the_run` |
