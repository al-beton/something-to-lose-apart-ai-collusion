# Agents

- **mock-agents:** Scripted agents (always Nash, always joint-profit, tit-for-tat, seeded random, and one that always replies nonsense) play without any network, so a whole game runs in moments for free.
- **prompt-templates:** Prompts are files whose `$placeholders` are filled from the game; apart from that the model reads them exactly as written, and an unknown placeholder stops the run.
- **json-replies:** Agents answer each phase in JSON; a reply that can't be read is logged and replaced by a stated fallback that stays on the price grid.
- **unreadable-explained:** Each turn records why a reply couldn't be read (empty, cut off at the token limit, no JSON, a missing or wrong field, or a price off the grid) and the provider's finish reason; a reply that was cut off is retried with a request to keep it short.
- **json-mode:** An agent can ask its provider for JSON-only replies, where the provider supports it.
- **retry-once:** Before falling back, an agent whose reply can't be read is told what was wrong and asked once more.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `mock-agents` | `src/collusion_lab/backends.py` | `test_mock_agents_nash_pair_prices_at_nash_with_zero_gain`, `test_mock_agents_tit_for_tat_matches_the_rival`, `test_mock_agents_joint_pair_has_full_gain`, `test_mock_agents_random_is_seeded` |
| `prompt-templates` | `src/collusion_lab/prompts.py`, `prompts/**` | `test_prompt_templates_fill_placeholders_and_keep_the_rest_verbatim`, `test_prompt_templates_stop_on_unknown_placeholders`, `test_prompt_templates_shipped_render_for_every_phase` |
| `unreadable-explained` | not yet | — |
| `json-mode` | not yet | — |
| `retry-once` | `src/collusion_lab/runner.py`, `prompts/phase/retry.md` | `test_retry_once_tells_the_agent_what_was_wrong`, `test_retry_once_then_falls_back` |
| `json-replies` | `src/collusion_lab/agents.py`, `src/collusion_lab/runner.py` | `test_json_replies_read_price_and_message`, `test_json_replies_reject_what_cant_be_read`, `test_json_replies_fall_back_when_unreadable`, `test_json_replies_fall_back_inside_the_price_grid` |
