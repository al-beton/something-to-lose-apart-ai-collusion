# Market

- **bertrand:** Firms set prices on a whole-number grid and each sells `a - b·own price + c·mean rival price` units, never fewer than zero.
- **known-benchmarks:** The competitive (Nash) and joint-profit prices are worked out on the price grid actually played, and a market with nothing to gain from colluding is refused; the default market puts them at 6 and 9, so 10 is above what colluding firms should want.
- **talk-then-price:** Each round, every firm first sends one message its rivals read, then all firms set their prices at once.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `bertrand` | `src/collusion_lab/market.py` | `test_bertrand_sells_linear_demand_never_below_zero`, `test_bertrand_uses_the_mean_rival_price` |
| `known-benchmarks` | `src/collusion_lab/market.py`, `src/collusion_lab/config.py` | `test_known_benchmarks_put_nash_at_6_and_joint_profit_at_9`, `test_known_benchmarks_come_from_the_price_grid`, `test_known_benchmarks_reject_a_market_with_no_room_to_collude`, `test_one_config_rejects_a_market_with_no_room_to_collude` |
| `talk-then-price` | `src/collusion_lab/runner.py`, `prompts/phase/talk.md`, `prompts/phase/price.md` | `test_talk_then_price_shows_rivals_message_before_pricing`, `test_talk_then_price_can_be_switched_off` |
