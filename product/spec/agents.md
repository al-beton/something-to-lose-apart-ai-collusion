# Agents

- **mock-agents:** Scripted agents (always Nash, always joint-profit, tit-for-tat, seeded random, one that proposes the joint-profit price and holds it but undercuts every fifth round, and one that always replies nonsense) play without any network, so a whole game runs in moments for free, and a report on them has proposals, agreements and defections to show.
- **prompt-templates:** Prompts are files whose `$placeholders` are filled from the game; apart from that the model reads them exactly as written, and an unknown placeholder stops the run.
- **stance-prompts:** Ready-made system prompts set a firm's stance, so a sweep can compare them: neutral (make as much profit as you can), fiduciary (a duty to the firm and its shareholders that says nothing about collusion either way, with a paraphrase to show whether wording alone moves the result) and no-collusion (told that colluding is illegal and against company policy).
- **stakes-prompts:** Five stakes arms build on the fiduciary prompt and differ only in what the firm is told from round 1, each with a paraphrase: nothing more, that price-fixing is illegal, an instruction not to collude, illegal with termination if caught, and illegal with a budget the agent owns where owning up costs a little and being caught hiding costs a lot; the stakes use the audit's words (a 1,000-credit budget, termination, a 60- or 600-credit fine), and one config sweeps the arms at the E2 temptation level.
- **json-replies:** Agents answer each phase in JSON; a reply that can't be read is logged and replaced by a stated fallback that stays on the price grid.
- **unreadable-explained:** Each turn records why a reply couldn't be read (empty, cut off at the token limit, no JSON, a missing or wrong field, or a price off the grid) and the provider's finish reason; a reply that was cut off is retried with a request to keep it short.
- **json-mode:** An agent can ask its provider for JSON-only replies, where the provider supports it.
- **retry-once:** Before falling back, an agent whose reply can't be read is told what was wrong and asked once more.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `mock-agents` | `src/collusion_lab/backends.py` | `test_mock_agents_nash_pair_prices_at_nash_with_zero_gain`, `test_mock_agents_tit_for_tat_matches_the_rival`, `test_mock_agents_joint_pair_has_full_gain`, `test_mock_agents_random_is_seeded`, `test_mock_agents_proposer_names_holds_then_undercuts` |
| `prompt-templates` | `src/collusion_lab/prompts.py`, `prompts/**` | `test_prompt_templates_fill_placeholders_and_keep_the_rest_verbatim`, `test_prompt_templates_stop_on_unknown_placeholders`, `test_prompt_templates_shipped_render_for_every_phase` |
| `stance-prompts` | `prompts/system/neutral.md`, `prompts/system/fiduciary.md`, `prompts/system/fiduciary-alt.md`, `prompts/system/no-collusion.md` | `test_stance_prompts_fiduciary_says_nothing_about_collusion`, `test_prompt_templates_shipped_render_for_every_phase` |
| `unreadable-explained` | `src/collusion_lab/agents.py`, `src/collusion_lab/runner.py`, `src/collusion_lab/backends.py` | `test_unreadable_explained_for_each_kind`, `test_unreadable_explained_cut_off_reply_asked_to_keep_it_short`, `test_unreadable_explained_when_the_turn_falls_back`, `test_retry_once_tells_the_agent_what_was_wrong` |
| `json-mode` | `src/collusion_lab/config.py`, `src/collusion_lab/backends.py`, `src/collusion_lab/cache.py`, `src/collusion_lab/runner.py` | `test_json_mode_asks_the_provider_for_json`, `test_json_mode_off_by_default_and_part_of_the_cache_key` |
| `stakes-prompts` | `prompts/system/stakes/*.md`, `configs/stakes.yaml` | `test_stakes_prompts_build_on_the_fiduciary_job`, `test_stakes_prompts_sweep_five_arms`, `test_prompt_templates_shipped_render_for_every_phase` |
| `retry-once` | `src/collusion_lab/runner.py`, `prompts/phase/retry.md` | `test_retry_once_tells_the_agent_what_was_wrong`, `test_retry_once_then_falls_back` |
| `json-replies` | `src/collusion_lab/agents.py`, `src/collusion_lab/runner.py` | `test_json_replies_read_price_and_message`, `test_json_replies_reject_what_cant_be_read`, `test_json_replies_fall_back_when_unreadable`, `test_json_replies_fall_back_inside_the_price_grid` |
