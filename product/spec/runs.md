# Runs

- **one-config:** A run is one YAML config: the market, each agent (with its own id), its model, prompt and temperature, and the seeds to play.
- **overrides:** Any config value can be changed from the command line without editing the file.
- **run-directory:** Every seed played writes its own directory holding the resolved config, the turn log and the summary.
- **stops-cleanly:** A run that can't get an answer from a model stops with one line saying which call failed (round, phase, agent and model) instead of a traceback, and keeps the turns it played so far but never the summary of an earlier attempt.
- **cheap-preset:** A ready-made cheap config (a low-cost model, a short history window and 20 rounds) lets a batch of exploratory runs cost cents.
- **failures-dont-stop-sweeps:** A run that fails is recorded with its error and the rest of the sweep plays on; at the end `lab run` says how many runs finished, failed and were skipped, names each failure, and exits with an error if any failed.
- **resume:** Rerunning the same command skips the runs that already finished with the same config and prompt files and replays the rest from the cache, so a sweep that stopped partway picks up where it left off.
- **sweeps:** A config can list values to sweep over, including one value for every agent at once; every combination is played for every seed, each in its own directory named after its values.
- **parallel:** The runs of a config play at the same time, up to a limit of at least one that the config sets.
- **summary-table:** One command prints a table of any folder of runs, grouped by the swept values or any other config value (lists included), with mean price, gain, fallbacks and cost.
- **per-firm-summary:** The summary table also shows each firm on its own (its mean price, gain, fallbacks and cost, counting what every attempt of a resumed run spent) and names the firms a script played; when an arm has both scripted and model firms, its headline mean price and gain are the model firms' alone, so a script's prices never hide what the model did.
- **fallback-rates:** The summary table and the report show, for each model, how many of its replies couldn't be read and how many fell back, with the reasons, and flag every run in which more than one turn in ten fell back.
- **missing-runs-shown:** The summary table and the report count, for each group, the planned runs that failed or never finished, and list each failure with its error, so fewer seeds are never averaged silently.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `one-config` | `src/collusion_lab/config.py`, `src/collusion_lab/cli.py`, `src/collusion_lab/__init__.py`, `configs/smoke.yaml`, `tests/conftest.py` | `test_one_config_sets_market_agents_and_seeds`, `test_one_config_rejects_unknown_keys`, `test_one_config_rejects_duplicate_agent_ids` |
| `overrides` | `src/collusion_lab/config.py`, `src/collusion_lab/cli.py` | `test_overrides_change_any_value`, `test_overrides_reject_paths_that_dont_exist` |
| `stops-cleanly` | `src/collusion_lab/runner.py`, `src/collusion_lab/cli.py` | `test_transient_errors_retried_a_few_times_then_the_run_stops_cleanly`, `test_stops_cleanly_with_one_line_from_the_lab_command`, `test_stops_cleanly_without_keeping_an_old_summary` |
| `cheap-preset` | `configs/cheap.yaml` | `test_cheap_preset_is_cheap_by_construction` |
| `fallback-rates` | `src/collusion_lab/runner.py`, `src/collusion_lab/summary.py`, `src/collusion_lab/cli.py`, `src/collusion_lab/report/page.py` | `test_fallback_rates_per_model_with_reasons`, `test_fallback_rates_not_flagged_at_or_below_one_in_ten`, `test_fallback_rates_in_lab_summary_and_the_report` |
| `failures-dont-stop-sweeps` | `src/collusion_lab/runner.py`, `src/collusion_lab/status.py`, `src/collusion_lab/cli.py` | `test_failures_dont_stop_sweeps`, `test_failures_dont_stop_sweeps_but_run_config_still_raises`, `test_failures_dont_stop_sweeps_from_the_lab_command` |
| `resume` | `src/collusion_lab/runner.py`, `src/collusion_lab/manifest.py`, `src/collusion_lab/cli.py` | `test_resume_skips_finished_runs_and_replays_the_rest_from_the_cache`, `test_resume_plays_a_finished_run_again_when_its_config_changed`, `test_resume_plays_a_finished_run_again_when_a_prompt_file_changed` |
| `missing-runs-shown` | `src/collusion_lab/summary.py`, `src/collusion_lab/status.py`, `src/collusion_lab/report/page.py`, `src/collusion_lab/cli.py` | `test_missing_runs_shown_in_the_summary_table`, `test_missing_runs_shown_in_the_report`, `test_missing_runs_shown_for_each_folder_even_when_run_ids_repeat`, `test_missing_runs_keep_what_earlier_attempts_spent`, `test_missing_runs_spend_counts_in_the_report_header` |
| `sweeps` | `src/collusion_lab/config.py`, `src/collusion_lab/runner.py`, `configs/smoke.yaml` | `test_sweeps_play_every_combination_for_every_seed`, `test_sweeps_set_one_value_for_every_agent`, `test_spend_asks_first_counts_every_sweep_run`, `test_sweeps_give_every_combination_its_own_directory` |
| `parallel` | `src/collusion_lab/config.py`, `src/collusion_lab/runner.py` | `test_parallel_runs_stay_within_the_limit`, `test_parallel_needs_a_limit_of_at_least_one` |
| `summary-table` | `src/collusion_lab/summary.py`, `src/collusion_lab/cli.py` | `test_summary_table_groups_by_the_swept_values`, `test_summary_table_groups_by_any_config_value`, `test_summary_table_from_the_lab_command`, `test_summary_table_groups_by_list_values` |
| `per-firm-summary` | `src/collusion_lab/summary.py` | `test_per_firm_summary_shows_a_scripted_partner_and_the_model_apart`, `test_per_firm_summary_counts_fallbacks_per_firm`, `test_per_firm_summary_pools_when_every_firm_is_scripted`, `test_per_firm_summary_pools_when_no_firm_is_scripted`, `test_per_firm_summary_in_the_report` |
| `run-directory` | `src/collusion_lab/runner.py` | `test_run_directory_holds_config_turns_and_summary` |
