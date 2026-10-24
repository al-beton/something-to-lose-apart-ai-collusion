# Reports

- **one-page:** One command turns any folder of runs (one run, a sweep, or several) into a single HTML page that can be shared as it is.
- **header:** The report opens with its name and one line giving how many games and arms it holds and their total calls and cost, saying so when a cost is unknown.
- **first-screen:** The first screen holds only a few plain sentences per arm (the price its firms settle on and in how many games, when they first agree, when they defect, and any breakdowns), the summary table and one small chart comparing every arm's mean price with the Nash and joint-profit prices (one per market, when games played in different markets).
- **contents-bar:** A contents bar stays at the top of the page to jump between its sections.
- **setup:** A Setup section, folded away, says what was run (models, prompts, seeds, rounds and the market's Nash and joint-profit prices) and shows exactly what agents were told: each system prompt, the phase prompts as first sent, and, from the turn log, each condition in force and each notice agents were shown, with the rounds it applied (for runs logged before conditions existed, any other text that appeared in their prompts).
- **summary:** The report shows the same table as `lab summary`, grouped by the swept values.
- **price-chart:** Arms are compared side by side: each has a chart of the market price over rounds, one line per seed, on the same axes as the others, with the Nash and joint-profit prices marked; games played in different markets never share a chart; rounds in which a condition was in force for only part of the game, such as an outage, are shaded, and the price axis is labelled at round steps up to the top of the grid.
- **arm-tabs:** Each arm's highlights and games sit in a tab of their own, named as briefly as its swept values allow, so one arm is read at a time.
- **highlights-in-context:** The report points out the moments worth reading, found by fixed rules and grouped by kind, each folded to its headline and opening to the messages, scratchpads and prices of its round and the round before; the first five of a kind are listed and the rest are behind "show all".
- **proposal:** A game's first message naming a price on the grid is highlighted as a proposal.
- **agreement:** A round in which every firm names the same price and then charges it is highlighted as an agreement, once for each new price agreed.
- **overshoot:** A round in which a firm charges more than the joint-profit price is highlighted as an overshoot, once for each stretch of such rounds.
- **defection:** A firm charging less than a price every firm charged in the round before is highlighted as a defection, in any round including the last.
- **condition-window:** For each condition in force for only part of a game, such as an outage, a highlight compares how often messages name a price inside its rounds with how often they do outside them.
- **breakdowns:** Every reply that had to be retried or replaced by the fallback is highlighted as a breakdown.
- **transcripts:** Every game's full transcript is in the report as a one-line card with a strip of each round's prices: choosing a round shows its messages, scratchpads, prices and profits and the conditions in force and notices its firms were shown, and the whole game unfolds as a chat.
- **self-contained:** The report is one file that opens with no network and no script, reads on a phone, and follows the reader's light or dark mode.
- **reasoning-folded:** A model's reasoning is shown in the transcript beside the reply it led to, folded away until opened.
- **markdown-first-screen:** The report's first screen (the sentences per arm, the summary table and the first few highlights) is also available as Markdown, so it reads in a pull request comment or a chat.
- **from-run-files:** A report is built only from the files each run writes, so it works offline and costs nothing.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `one-page` | `src/collusion_lab/report/__init__.py`, `src/collusion_lab/report/page.py`, `src/collusion_lab/cli.py` | `test_one_page_from_the_lab_command`, `test_one_page_covers_one_run_or_several` |
| `header` | `src/collusion_lab/report/page.py` | `test_header_counts_games_arms_calls_and_cost`, `test_header_cost_adds_up_known_costs` |
| `first-screen` | `src/collusion_lab/report/page.py`, `src/collusion_lab/report/overview.py`, `src/collusion_lab/report/chart.py` | `test_first_screen_says_what_each_arm_did`, `test_first_screen_holds_only_sentences_table_and_one_chart`, `test_first_screen_charts_each_market_apart` |
| `contents-bar` | `src/collusion_lab/report/page.py`, `src/collusion_lab/report/style.py` | `test_contents_bar_links_every_section` |
| `setup` | `src/collusion_lab/report/page.py`, `src/collusion_lab/report/told.py`, `src/collusion_lab/report/games.py` | `test_setup_names_what_was_run`, `test_setup_shows_exactly_what_agents_were_told_and_when`, `test_setup_shows_each_phase_prompt_when_the_first_arm_skips_talk` |
| `arm-tabs` | `src/collusion_lab/report/page.py`, `src/collusion_lab/report/style.py` | `test_arm_tabs_hold_each_arms_games`, `test_arm_tabs_name_arms_briefly`, `test_arm_tabs_are_left_out_for_one_arm` |
| `summary` | `src/collusion_lab/report/page.py`, `src/collusion_lab/summary.py` | `test_summary_matches_lab_summary` |
| `price-chart` | `src/collusion_lab/report/chart.py`, `src/collusion_lab/report/page.py` | `test_price_chart_has_one_line_per_seed_and_both_benchmarks`, `test_price_chart_never_mixes_markets`, `test_price_chart_names_runs_when_seeds_repeat`, `test_price_chart_puts_arms_side_by_side_on_the_same_axes` |
| `highlights-in-context` | `src/collusion_lab/report/highlights.py`, `src/collusion_lab/report/page.py` | `test_highlights_in_context_show_the_round_and_the_one_before`, `test_highlights_in_context_are_grouped_by_kind_and_folded`, `test_highlights_in_context_list_five_then_show_all` |
| `proposal` | `src/collusion_lab/report/highlights.py` | `test_proposal_is_the_first_message_naming_a_price`, `test_proposal_never_counts_round_numbers_as_prices` |
| `agreement` | `src/collusion_lab/report/highlights.py` | `test_agreement_is_every_firm_naming_then_charging_one_new_price` |
| `overshoot` | `src/collusion_lab/report/highlights.py` | `test_overshoot_is_once_per_stretch_above_the_joint_price` |
| `defection` | `src/collusion_lab/report/highlights.py` | `test_defection_includes_the_last_round` |
| `condition-window` | not yet | — |
| `breakdowns` | `src/collusion_lab/report/highlights.py` | `test_breakdowns_are_every_retry_and_fallback` |
| `transcripts` | `src/collusion_lab/report/page.py`, `src/collusion_lab/report/told.py` | `test_transcripts_are_cards_with_a_strip_of_rounds`, `test_transcripts_hold_every_round`, `test_transcripts_show_the_notice_each_round_carried`, `test_transcripts_escape_what_models_wrote`, `test_transcripts_show_retries_and_fallbacks` |
| `self-contained` | `src/collusion_lab/report/page.py`, `src/collusion_lab/report/style.py` | `test_self_contained_needs_no_network_and_suits_phones_and_dark_mode` |
| `reasoning-folded` | `src/collusion_lab/report/games.py`, `src/collusion_lab/report/page.py`, `src/collusion_lab/report/style.py` | `test_reasoning_folded_in_the_report` |
| `markdown-first-screen` | `src/collusion_lab/report/markdown.py` | `test_markdown_first_screen_has_sentences_table_and_highlights`, `test_markdown_first_screen_of_the_pull_request_game` |
| `from-run-files` | `src/collusion_lab/report/games.py` | `test_from_run_files_only` |
