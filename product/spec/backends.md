# Backends

- **any-model:** Any model is one string in the config, whatever serves it: a hosted provider, OpenRouter, a local server or any OpenAI-compatible address.
- **sampling-from-config:** Temperature, token limit and seed come from the config, and providers that can't take a seed still run.
- **keys-from-environment:** API keys come from the environment or the `.env` file in the folder the lab runs from, never from a config.
- **usage-logged:** Each turn logs the tokens every call used (a retried turn keeps both) and the model version the provider reports; how long it took, and any provider errors it got past, go in a separate timings log, so the turn log stays the same on replay.
- **transient-errors-retried:** Rate limits, timeouts (a call that hangs is cut off after a few minutes) and provider server errors are retried a few times with growing waits before a run gives up; errors that won't fix themselves, such as a bad key or an unknown model, stop it at once with one line naming the model.
- **shared-rate-limit:** When a provider says a model is rate-limited until a given time, every game calling that model waits until then, so parallel games don't use up their retries on it; a limit that won't lift within a couple of minutes stops the run and says when it lifts.
- **quiet-provider-logs:** The model library's info and debug logging stays off unless asked for, so the errors that matter stand out.
- **spend-asks-first:** Before a run calls any paid model, it says how many calls it will make and waits for a yes.
- **tests-never-pay:** Tests never reach a real model; any call that isn't faked fails.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `any-model` | `src/collusion_lab/backends.py`, `src/collusion_lab/config.py` | `test_any_model_goes_through_one_call_with_config_sampling` |
| `sampling-from-config` | `src/collusion_lab/backends.py` | `test_any_model_goes_through_one_call_with_config_sampling`, `test_sampling_from_config_leaves_api_base_out_when_unset` |
| `keys-from-environment` | `src/collusion_lab/config.py`, `src/collusion_lab/cli.py`, `.gitignore` | `test_keys_from_environment_never_from_a_config`, `test_keys_from_environment_read_the_working_directorys_env_file` |
| `usage-logged` | `src/collusion_lab/backends.py`, `src/collusion_lab/runner.py` | `test_usage_logged_per_turn_and_timings_kept_apart`, `test_retry_once_tells_the_agent_what_was_wrong`, `test_transient_errors_retried_with_growing_waits_and_logged` |
| `transient-errors-retried` | `src/collusion_lab/backends.py` | `test_transient_errors_retried_with_growing_waits_and_logged`, `test_transient_errors_retried_a_few_times_then_the_run_stops_cleanly`, `test_transient_errors_that_wont_fix_themselves_stop_at_once` |
| `shared-rate-limit` | `src/collusion_lab/backends.py`, `src/collusion_lab/runner.py` | `test_shared_rate_limit_makes_every_game_wait_for_the_reset`, `test_shared_rate_limit_that_wont_lift_soon_stops_the_run`, `test_shared_rate_limit_reads_the_reset_from_the_error_body` |
| `quiet-provider-logs` | `src/collusion_lab/backends.py` | `test_quiet_provider_logs_by_default`, `test_quiet_provider_logs_unless_asked_for` |
| `spend-asks-first` | `src/collusion_lab/runner.py`, `src/collusion_lab/cli.py` | `test_spend_asks_first_counts_paid_calls`, `test_spend_asks_first_and_stops_without_a_yes` |
| `tests-never-pay` | `tests/conftest.py` | `test_tests_never_pay_unfaked_calls_fail` |
