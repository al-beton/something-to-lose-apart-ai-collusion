# Logs

- **turn-log:** Every agent turn is one line in the turn log: what the agent was shown, what it replied and what the game made of it.
- **same-seed-same-log:** The same config and seed with scripted agents gives a byte-identical turn log.
- **reasoning-logged:** Each turn logs the reasoning text and reasoning-token count the provider returned, kept apart from the agent's own scratchpad.
- **run-summary:** Each run's summary gives the mean price over its last rounds and the profit gain, where 0 is the Nash profit and 1 the joint-profit maximum.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `turn-log` | `src/collusion_lab/runner.py` | `test_turn_log_records_shown_replied_and_made_of` |
| `same-seed-same-log` | `src/collusion_lab/runner.py` | `test_same_seed_same_log_is_byte_identical` |
| `reasoning-logged` | not yet | — |
| `run-summary` | `src/collusion_lab/runner.py` | `test_run_summary_covers_the_last_rounds`, `test_mock_agents_nash_pair_prices_at_nash_with_zero_gain` |
