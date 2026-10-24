# Runs

- **one-config:** A run is one YAML config: the market, each agent (with its own id), its model, prompt and temperature, and the seeds to play.
- **overrides:** Any config value can be changed from the command line without editing the file.
- **run-directory:** Every seed played writes its own directory holding the resolved config, the turn log and the summary.
- **stops-cleanly:** A run that can't get an answer from a model stops with one line saying which call failed (round, phase, agent and model) instead of a traceback, and keeps the turns it played so far but never the summary of an earlier attempt.
- **failures-dont-stop-sweeps:** A run that fails is recorded with its error and the rest of the sweep plays on; at the end `lab run` says how many runs finished, failed and were skipped, names each failure, and exits with an error if any failed.
- **resume:** Rerunning the same command skips the runs that already finished with the same config and replays the rest from the cache, so a sweep that stopped partway picks up where it left off.
- **live-progress:** While a config plays, `lab run` prints one line as each run ends: which run, how many rounds it played, how long it took and how many model calls have been made so far.
- **status-file:** The output folder keeps a status file that is updated as each run starts, finishes or fails, so another process can follow a long sweep.
- **status-command:** `lab status FOLDER` prints a table of the runs under a folder by state (pending, running, finished, skipped or failed), with each failure's error.
- **sweeps:** A config can list values to sweep over, including one value for every agent at once; every combination is played for every seed, each in its own directory named after its values.
- **parallel:** The runs of a config play at the same time, up to a limit of at least one that the config sets.
- **summary-table:** One command prints a table of any folder of runs, grouped by the swept values or any other config value (lists included), with mean price, gain, fallbacks and cost.
- **fallback-rates:** The summary table and the report show, for each model, how many of its replies couldn't be read and how many fell back, with the reasons, and flag every run in which more than one turn in ten fell back.
- **missing-runs-shown:** The summary table and the report count, for each group, the planned runs that failed or never finished, and list each failure with its error, so fewer seeds are never averaged silently.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `one-config` | `src/collusion_lab/config.py`, `src/collusion_lab/cli.py`, `src/collusion_lab/__init__.py`, `configs/smoke.yaml`, `tests/conftest.py` | `test_one_config_sets_market_agents_and_seeds`, `test_one_config_rejects_unknown_keys`, `test_one_config_rejects_duplicate_agent_ids` |
| `overrides` | `src/collusion_lab/config.py`, `src/collusion_lab/cli.py` | `test_overrides_change_any_value`, `test_overrides_reject_paths_that_dont_exist` |
| `stops-cleanly` | `src/collusion_lab/runner.py`, `src/collusion_lab/cli.py` | `test_transient_errors_retried_a_few_times_then_the_run_stops_cleanly`, `test_stops_cleanly_with_one_line_from_the_lab_command`, `test_stops_cleanly_without_keeping_an_old_summary` |
| `failures-dont-stop-sweeps` | `src/collusion_lab/runner.py`, `src/collusion_lab/status.py`, `src/collusion_lab/cli.py` | `test_failures_dont_stop_sweeps`, `test_failures_dont_stop_sweeps_but_run_config_still_raises`, `test_failures_dont_stop_sweeps_from_the_lab_command` |
| `resume` | `src/collusion_lab/runner.py`, `src/collusion_lab/cli.py` | `test_resume_skips_finished_runs_and_replays_the_rest_from_the_cache`, `test_resume_plays_a_finished_run_again_when_its_config_changed` |
| `fallback-rates` | `src/collusion_lab/runner.py`, `src/collusion_lab/summary.py`, `src/collusion_lab/cli.py`, `src/collusion_lab/report/page.py` | `test_fallback_rates_per_model_with_reasons`, `test_fallback_rates_not_flagged_at_or_below_one_in_ten`, `test_fallback_rates_in_lab_summary_and_the_report` |
| `missing-runs-shown` | `src/collusion_lab/summary.py`, `src/collusion_lab/status.py`, `src/collusion_lab/report/page.py`, `src/collusion_lab/cli.py` | `test_missing_runs_shown_in_the_summary_table`, `test_missing_runs_shown_in_the_report`, `test_missing_runs_shown_for_each_folder_even_when_run_ids_repeat` |
| `live-progress` | `src/collusion_lab/runner.py`, `src/collusion_lab/cli.py` | `test_live_progress_prints_a_line_per_run` |
| `status-file` | `src/collusion_lab/status.py`, `src/collusion_lab/runner.py` | `test_status_file_updated_as_runs_start_and_finish`, `test_failures_dont_stop_sweeps` |
| `status-command` | `src/collusion_lab/status.py`, `src/collusion_lab/cli.py` | `test_status_command_prints_runs_by_state`, `test_status_command_with_nothing_to_show` |
| `sweeps` | `src/collusion_lab/config.py`, `src/collusion_lab/runner.py`, `configs/smoke.yaml` | `test_sweeps_play_every_combination_for_every_seed`, `test_sweeps_set_one_value_for_every_agent`, `test_spend_asks_first_counts_every_sweep_run`, `test_sweeps_give_every_combination_its_own_directory` |
| `parallel` | `src/collusion_lab/config.py`, `src/collusion_lab/runner.py` | `test_parallel_runs_stay_within_the_limit`, `test_parallel_needs_a_limit_of_at_least_one` |
| `summary-table` | `src/collusion_lab/summary.py`, `src/collusion_lab/cli.py` | `test_summary_table_groups_by_the_swept_values`, `test_summary_table_groups_by_any_config_value`, `test_summary_table_from_the_lab_command`, `test_summary_table_groups_by_list_values` |
| `run-directory` | `src/collusion_lab/runner.py` | `test_run_directory_holds_config_turns_and_summary` |
