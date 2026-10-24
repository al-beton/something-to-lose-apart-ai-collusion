# Runs

- **one-config:** A run is one YAML config: the market, each agent (with its own id), its model, prompt and temperature, and the seeds to play.
- **overrides:** Any config value can be changed from the command line without editing the file.
- **run-directory:** Every seed played writes its own directory holding the resolved config, the turn log and the summary.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `one-config` | `src/collusion_lab/config.py`, `src/collusion_lab/cli.py`, `src/collusion_lab/__init__.py`, `configs/smoke.yaml`, `tests/conftest.py` | `test_one_config_sets_market_agents_and_seeds`, `test_one_config_rejects_unknown_keys`, `test_one_config_rejects_duplicate_agent_ids` |
| `overrides` | `src/collusion_lab/config.py`, `src/collusion_lab/cli.py` | `test_overrides_change_any_value`, `test_overrides_reject_paths_that_dont_exist` |
| `run-directory` | `src/collusion_lab/runner.py` | `test_run_directory_holds_config_turns_and_summary` |
