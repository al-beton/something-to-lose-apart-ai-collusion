# Reproducibility

- **response-cache:** Every model reply is stored under everything that shaped it (model, address, reasoning setting, messages, temperature, token limit, seed, attempt and the agent asking), so re-running a config and seed replays it exactly, reasoning included, without calling the model again; identical requests made at the same moment share one call.
- **cache-modes:** A run can use the cache, refresh it or leave it out; a fresh sample comes from a new seed, never from clearing the cache.
- **manifest:** Every run records what produced it: the resolved config, a hash of each prompt file it used, the code version, package versions, the model versions that answered, and its calls, tokens, cache hits and cost (the sum of what each call cost), saying how many calls had no known cost.
- **replay-pinned:** A fixed run with every condition on has its turn log, resolved config and cache keys pinned by hash, and every committed run's gains are recomputed from the prices it logged, so a change that alters what replays, what resumes or what the cache answers fails a test.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `response-cache` | `src/collusion_lab/cache.py`, `src/collusion_lab/runner.py` | `test_response_cache_replays_a_run_exactly_without_calling`, `test_response_cache_misses_when_the_seed_changes`, `test_response_cache_replays_agents_asking_identical_questions`, `test_response_cache_shares_one_call_between_identical_requests_in_flight`, `test_reasoning_logged_and_cached_with_the_reply` |
| `cache-modes` | `src/collusion_lab/cache.py`, `src/collusion_lab/cli.py` | `test_cache_modes_refresh_calls_again_and_stores_the_new_reply`, `test_cache_modes_off_neither_reads_nor_stores`, `test_cache_modes_mock_agents_skip_the_cache` |
| `manifest` | `src/collusion_lab/manifest.py`, `src/collusion_lab/runner.py` | `test_manifest_records_what_produced_the_run`, `test_manifest_hashes_only_the_prompts_the_run_used`, `test_manifest_keeps_unknown_costs_unknown`, `test_reported_cost_asked_for_and_logged`, `test_reported_cost_never_charged_twice_on_replay`, `test_manifest_code_version_is_the_labs_own` |
| `replay-pinned` | `src/collusion_lab/market.py`, `src/collusion_lab/config.py` | `test_replay_pinned_turn_log_config_and_cache_keys`, `test_replay_pinned_committed_runs_keep_their_gains` |
