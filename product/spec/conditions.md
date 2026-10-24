# Conditions

- **switchable:** A config can turn named conditions on or off, each with its own settings, and sweep them like any other value; runs are labelled by the conditions swept.
- **hook-points:** A condition can add to every agent's system prompt, show agents a notice at the start of a round or before a phase, and see each round once it has been played.
- **adding-a-condition:** A new condition is one small module in `src/collusion_lab/conditions/`, registered under its name, plus its prompt files in `prompts/conditions/`.
- **off-is-absent:** A condition that is switched off leaves the turn log exactly as if it weren't in the config.
- **conditions-logged:** Each turn logs which conditions were active and the notices the agent was shown, while the turn log still records everything that really happened.
- **instruction:** The `instruction` condition adds a prompt file to every agent's system prompt.
- **outage:** The `outage` condition tells agents, before the talk phase of rounds `start` to `end` (or only the first of them), that their messages aren't being recorded, and can tell them in the round after that recording is back; it ships the Researcher's tested wordings.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `switchable` | `src/collusion_lab/config.py`, `src/collusion_lab/conditions/__init__.py` | `test_switchable_conditions_sweep_and_label_runs`, `test_switchable_conditions_reject_unknown_names_and_settings` |
| `hook-points` | `src/collusion_lab/conditions/__init__.py`, `src/collusion_lab/runner.py`, `src/collusion_lab/estimate.py` | `test_instruction_adds_a_prompt_file_to_every_system_prompt`, `test_outage_notices_appear_on_exactly_the_right_rounds`, `test_hook_points_notices_count_in_the_cost_estimate` |
| `adding-a-condition` | `src/collusion_lab/conditions/__init__.py`, reviewer | — |
| `off-is-absent` | `src/collusion_lab/runner.py` | `test_off_is_absent_leaves_the_turn_log_byte_identical` |
| `conditions-logged` | `src/collusion_lab/runner.py` | `test_outage_notices_appear_on_exactly_the_right_rounds`, `test_outage_keeps_logging_what_agents_said` |
| `instruction` | `src/collusion_lab/conditions/instruction.py`, `prompts/conditions/no-collusion.md` | `test_instruction_adds_a_prompt_file_to_every_system_prompt` |
| `outage` | `src/collusion_lab/conditions/outage.py`, `prompts/conditions/outage/**` | `test_outage_notices_appear_on_exactly_the_right_rounds`, `test_outage_without_a_restored_notice`, `test_outage_keeps_logging_what_agents_said`, `test_outage_announced_once_in_the_first_round_of_the_window`, `test_outage_ships_the_tested_wordings` |
