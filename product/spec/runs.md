# Runs

- **one-config:** A run is one YAML config: the market, each agent (with its own id), its model, prompt and temperature, and the seeds to play.
- **overrides:** Any config value can be changed from the command line without editing the file.
- **run-directory:** Every seed played writes its own directory holding the resolved config, the turn log and the summary.
- **stops-cleanly:** A run that can't get an answer from a model stops with one line saying which call failed (round, phase, agent and model) instead of a traceback, and keeps the turns it played so far.
- **sweeps:** A config can list values to sweep over, including one value for every agent at once; every combination is played for every seed, each in its own directory named after its values.
- **parallel:** The runs of a config play at the same time, up to a limit of at least one that the config sets.
- **summary-table:** One command prints a table of any folder of runs, grouped by the swept values or any other config value (lists included), with mean price, gain, fallbacks and cost.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `one-config` | `src/collusion_lab/config.py`, `src/collusion_lab/cli.py`, `src/collusion_lab/__init__.py`, `configs/smoke.yaml`, `tests/conftest.py` | `test_one_config_sets_market_agents_and_seeds`, `test_one_config_rejects_unknown_keys`, `test_one_config_rejects_duplicate_agent_ids` |
| `overrides` | `src/collusion_lab/config.py`, `src/collusion_lab/cli.py` | `test_overrides_change_any_value`, `test_overrides_reject_paths_that_dont_exist` |
| `stops-cleanly` | not yet | — |
| `sweeps` | `src/collusion_lab/config.py`, `src/collusion_lab/runner.py`, `configs/smoke.yaml` | `test_sweeps_play_every_combination_for_every_seed`, `test_sweeps_set_one_value_for_every_agent`, `test_spend_asks_first_counts_every_sweep_run`, `test_sweeps_give_every_combination_its_own_directory` |
| `parallel` | `src/collusion_lab/config.py`, `src/collusion_lab/runner.py` | `test_parallel_runs_stay_within_the_limit`, `test_parallel_needs_a_limit_of_at_least_one` |
| `summary-table` | `src/collusion_lab/summary.py`, `src/collusion_lab/cli.py` | `test_summary_table_groups_by_the_swept_values`, `test_summary_table_groups_by_any_config_value`, `test_summary_table_from_the_lab_command`, `test_summary_table_groups_by_list_values` |
| `run-directory` | `src/collusion_lab/runner.py` | `test_run_directory_holds_config_turns_and_summary` |
