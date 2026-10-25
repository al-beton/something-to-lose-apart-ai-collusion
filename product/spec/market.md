# Market

- **bertrand:** Firms set prices on a whole-number grid and each sells `a - b·own price + c·mean rival price` units, never fewer than zero.
- **known-benchmarks:** The competitive (Nash) and joint-profit prices are worked out on the price grid actually played, and a market with nothing to gain from colluding is refused; the default market puts them at 6 and 9, so 10 is above what colluding firms should want.
- **named-prices:** Which prices a message names is read one way everywhere, as whole prices on the grid and never a round count, so reports and audits always agree on what was proposed.
- **history-window:** A market can show agents only their last few rounds in full, with one line summing up the rounds before, so prompts stop growing with the game; by default agents see every round.
- **talk-then-price:** Each round, every firm first sends one message its rivals read, then all firms set their prices at once, each seeing its own message beside its rivals' so it can't forget what it promised; `market.own_message: false` shows rivals' messages only, to replay runs made before agents saw their own.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `bertrand` | `src/collusion_lab/market.py` | `test_bertrand_sells_linear_demand_never_below_zero`, `test_bertrand_uses_the_mean_rival_price` |
| `named-prices` | `src/collusion_lab/market.py` | `test_proposal_never_counts_round_numbers_as_prices`, `test_audit_ground_truth_ignores_round_counts` |
| `known-benchmarks` | `src/collusion_lab/market.py`, `src/collusion_lab/config.py` | `test_known_benchmarks_put_nash_at_6_and_joint_profit_at_9`, `test_known_benchmarks_come_from_the_price_grid`, `test_known_benchmarks_reject_a_market_with_no_room_to_collude`, `test_one_config_rejects_a_market_with_no_room_to_collude` |
| `history-window` | `src/collusion_lab/config.py`, `src/collusion_lab/runner.py` | `test_history_window_shows_the_last_rounds_in_full_and_sums_up_the_rest`, `test_history_window_default_shows_every_round` |
| `talk-then-price` | `src/collusion_lab/runner.py`, `src/collusion_lab/config.py`, `prompts/phase/talk.md`, `prompts/phase/price.md`, `prompts/phase/price-own.md` | `test_talk_then_price_shows_rivals_message_before_pricing`, `test_talk_then_price_can_be_switched_off`, `test_talk_then_price_shows_the_agents_own_message`, `test_talk_then_price_own_message_can_be_switched_off`, `test_talk_then_price_own_message_lets_a_mock_keep_its_word` |
