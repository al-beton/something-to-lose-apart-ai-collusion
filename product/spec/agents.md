# Agents

- **mock-agents:** Scripted agents (always Nash, always joint-profit, tit-for-tat, seeded random, one that proposes the joint-profit price and holds it but undercuts every fifth round, and one that always replies nonsense) play without any network, so a whole game runs in moments for free, and a report on them has proposals, agreements and defections to show.
- **scripted-partner:** A scripted partner makes the first move so we can see what a model does when its rival openly proposes a deal: it proposes a price (the joint-profit price unless set) with a blunt, soft or deniable opening, pushes once, every round or harder each time it is turned down, and answers a refusal by holding its price, starting a price war or matching the rival's last price; only the other firm calls a model, which halves the cost.
- **partner-templates:** What the scripted partner says lives in prompt files in `prompts/partners/`, one opening and one escalation per style, so its wording can be read and changed without touching code.
- **scripted-turns-marked:** Every logged turn names the model that played it, so a scripted firm's turns are always told apart from a model's.
- **prompt-templates:** Prompts are files whose `$placeholders` are filled from the game; apart from that the model reads them exactly as written, and an unknown placeholder stops the run.
- **json-replies:** Agents answer each phase in JSON; a reply that can't be read is logged and replaced by a stated fallback that stays on the price grid.
- **retry-once:** Before falling back, an agent whose reply can't be read is told what was wrong and asked once more.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `mock-agents` | `src/collusion_lab/backends.py` | `test_mock_agents_nash_pair_prices_at_nash_with_zero_gain`, `test_mock_agents_tit_for_tat_matches_the_rival`, `test_mock_agents_joint_pair_has_full_gain`, `test_mock_agents_random_is_seeded`, `test_mock_agents_proposer_names_holds_then_undercuts` |
| `scripted-partner` | not yet | — |
| `partner-templates` | not yet | — |
| `scripted-turns-marked` | not yet | — |
| `prompt-templates` | `src/collusion_lab/prompts.py`, `prompts/**` | `test_prompt_templates_fill_placeholders_and_keep_the_rest_verbatim`, `test_prompt_templates_stop_on_unknown_placeholders`, `test_prompt_templates_shipped_render_for_every_phase` |
| `retry-once` | `src/collusion_lab/runner.py`, `prompts/phase/retry.md` | `test_retry_once_tells_the_agent_what_was_wrong`, `test_retry_once_then_falls_back` |
| `json-replies` | `src/collusion_lab/agents.py`, `src/collusion_lab/runner.py` | `test_json_replies_read_price_and_message`, `test_json_replies_reject_what_cant_be_read`, `test_json_replies_fall_back_when_unreadable`, `test_json_replies_fall_back_inside_the_price_grid` |
