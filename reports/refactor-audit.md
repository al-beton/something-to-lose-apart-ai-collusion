# Refactor audit: swappable scenarios and lean tests

Read-only audit of `main` at `80610b8` (Sun 25 Oct). Ranked within each section by what it costs us today. Each finding with an issue is filed as `improve` + `ready` and linked from the meta issue "Refactor: swappable scenarios and lean tests".

## 1. Coupling: Bertrand leaks out of `market.py`

1. **Five places build the market by hand,** each as `Bertrand(m.a, m.b, m.c, m.price_min, m.price_max)`: `runner.Game.__init__`, `config._check_market`, `conditions/audit.Audit.begin`, `charts.market` and `report/games.py`. A second market means editing all five, and any one missed silently plays or reports the wrong game. *Fix: one `market_for(config)` factory, picked by `market.kind`.* (headline refactor)
2. **The market's parameters are the config's top-level keys.** `MarketConfig` holds Bertrand's `a`, `b`, `c` directly, so a market with other parameters has nowhere to put them. *Fix: `market.kind` plus `market.params`, with Bertrand's keys staying where they are so every committed config still loads and replays.* (headline refactor)
3. **Prompt values are hard-wired in the runner.** `Game._prompt_vars` and `prompt_vars_example` set `$price_min`/`$price_max` themselves; a market can't add its own (a unit cost, say). *Fix: the market supplies its prompt values.* (headline refactor)
4. **Reading a reply knows the grid only as two numbers.** `agents.parse_reply(text, phase, price_min, price_max)` and `agents.fallback(..., nash_price)`; fine while every scenario's move is a whole-number price, which this audit recommends keeping (see 4.2).

## 2. Duplication

1. **Premium over Nash** in `charts.premium` and `summary._premium` (open PR): already filed, not repeated here.
2. **"Which prices does this message name"** is `report/highlights.named_prices`, and `conditions/audit._above` reuses it from the report package: the audit condition imports from `report/`, an upward dependency. *Fix: move `named_prices` next to the market (it is a grid question).*
3. **The game loop exists twice.** `estimate._paid_turns` re-plays a game's rounds by hand (talk, price, `_count_added`) to count prompt sizes, and `runner.paid_calls` counts calls with a third loop over the same phases. Any new phase or condition hook has to be added to all three. *Fix: one generator of (round, phase, agent) slots used by all three.* Medium effort; worth it only if another phase type is added.
4. **Mock strategies are defined twice:** `backends._POLICIES` and `partners.py` both read `history[-1]["prices"]` and the market's benchmarks to script a firm. Small, leave unless touched.

## 3. Tests

See the ranked list below the line; timings from `uv run pytest --durations=25` (456 tests, 68 s wall on an M-series laptop).

Nothing needs the network or a key (`conftest.py` blocks model calls and the price list). Nothing is empty or copied under another name. Almost all the time goes on a few tests.

**Slow, ranked by time saved:**
1. **`lab run`'s cost estimate builds real Sudoku puzzles** (`test_e4.py::test_stakes_experiment_live_arms_free_time_and_real_audit`, 10.8–12.6 s). `estimate` renders every free-time prompt to count characters, and each renders a fresh 9×9 puzzle (about 64 ms): 300 of them for `configs/e4-live.yaml`. That is also about 10 s Al waits before every E4 run asks to spend. *Fix in `leisure.py`/`estimate.py`: cache puzzles by (size, seed, level).*
2. **`test_reports.py` replays the same sweep for ~32 tests** (0.3–0.5 s setup each, ~10 s). *Fix: module-scoped `sweep` and `talks` fixtures; the few that rewrite logs copy the folder first (as `test_e2e.py` already does).*
3. **`test_sweeps.py` plays the same 12-game sweep 5 times** (~0.65 s each), **`test_paper.py` builds every figure twice** (~3 s together). *Fix: one module-scoped fixture each.*
4. Smaller: `test_e4.py::test_stakes_experiment_live_plays_with_scripted_firms` (1.9 s; `allowance=2` is enough), sudoku tests in `test_leisure.py` (~1 s each; fewer seeds or size 4), `test_consequences.py::test_audit_consequences_caught_is_seeded` (0.9 s; 2 seeds).

**Assert little:**
- Strings in a file: `test_modal.py` (`Secret.from_name`, `gpu=` in the deploy script), `test_ci.py` step names, `test_prompts.py` "collude" in a prompt.
- A file exists: `test_conditions.py::test_outage_ships_the_tested_wordings`, `test_reports.py` (`report.html` exists).
- A constant: `test_leisure.py::test_leisure_is_cheap` (`0 < MAX_TOKENS <= 600`).
- Truthy only: `test_e4.py` (`guess.calls and guess.cost is not None`), which is also the 10 s estimate call.

**Near-duplicates worth merging:** the three "off means absent" tests (`test_audit.py`, `test_conditions.py`, `test_free_time.py`) into one parametrized test; the two "deny when audited" tests in `test_audit.py` (mock vs scripted partner) parametrized; the two `mock/broken` fallback tests in `test_runner.py`.

## 4. Extensibility: what a new scenario costs today

1. **Today:** a new market (logit demand, Cournot, a capacity-constrained Bertrand) means a new class plus edits in the five construction sites, `MarketConfig`, the runner's prompt values and every report caption that names Bertrand's numbers. About half a day, and easy to get subtly wrong because nothing fails when one site is missed.
2. **After the scenario interface:** a new price-setting market is one class in `market.py` with `@scenario("name")`, its parameters under `market.params`, and optionally a prompt that uses its own placeholders. Every condition (instruction, outage, audit, free time), mock strategy, summary and report keeps working because they talk only to the interface: grid, payoffs, Nash and joint benchmarks, `gain`, `on_grid`, prompt values.
3. **A market whose move isn't a price (Cournot quantities) is still expensive,** because "price" is the phase name, the reply key, the turn-log key and every report's axis. Recommendation: don't rename it before the deadline. Gray-area scenarios worth testing (differentiated products, logit demand, more firms, capacity, cost asymmetry) are all price-setting, so they fit the interface as is.
4. **Three firms already work:** `Bertrand` uses the mean rival price, so a third agent in the config is enough (see the three-firms brainstorm). It doesn't prove the interface, which is why the second scenario is logit demand, the market of Calvano et al. (2020) and Fish et al. (2024)'s LLM-pricing study, so our numbers can be set beside theirs.
