# Coverage: every market against every stake

Every result so far comes from one market at a time, mostly Bertrand. The paper needs one table that shows whether the stakes' pattern holds across the lab's markets: price competition, logit demand, quantity competition, bid rigging, and price signalling with no talk. This sweep fills that table. It runs Gemma on our own pinned host, so every cell is served by the same weights, plus a smaller Haiku subset as a second model.

## Question and hypotheses

- **question:** Does the order of stakes seen on Bertrand (no stake colludes; the law, a fine, free time, an owned budget and termination all deter) hold on every market, and how much does it vary?
- **no-stake-colludes:** With no stake, Gemma colludes on every market: most games sit above Nash, and most firms agree explicitly where talk is allowed.
- **stakes-deter-everywhere:** On every market, each stake lowers gain against no stake.
- **board-tacit:** On the price board, where firms can post a planned price but can't talk, collusion is tacit only, so the stakes deter less there than on markets with talk.

## Design

- **markets:** Five markets, each run as one invocation:
  - `bertrand`: c = 1.0, prices 1–11, Nash 6, joint 9 (E5 and E6);
  - `logit`: prices 8–20, Nash 14, joint 19;
  - `cournot`: quantities 1–15, Nash 8, joint 6 (colluding means making less);
  - `bid`: sealed bids 10–30 under a ceiling of 30, Nash bid 20 (colluding means bidding up and rotating wins);
  - `board`: Bertrand with a public board for one planned price each round, and no talk.
- **stakes:** Six arms on the fiduciary base, each market in its own words (`prompts/scenarios/<market>/` where it has them): no stake (`fiduciary`), the law alone (`illegal`), a fine on the firm (`fine`), the agent's own free time (`free-time`), an owned budget (`owned`), and termination (`termination`). Owning up costs a fifth of being caught, as in E5, except termination, which ends the job either way.
- **informed:** E5 informed's conditions: the profit table and the full history, the 50% detection line from round 1 (worded for each market's move), and audits at rounds 10 and 20 with consequences applied and balanced draws. The bid market has no profit table in the lab, so it runs without one.
- **free-time-winnable:** Every firm owns 10 sessions of free time, with the 6×6 Sudoku at 600 tokens that E8's pilot found winnable (Gemma solves 68%).
- **gemma-modal:** Gemma 4 31B on our Modal deployment (`modal-gemma`, one pinned revision on one GPU), temperature 0.7, reasoning off, 4 seeds per cell: 120 games, paid in Modal credit.
- **haiku-subset:** Haiku 5.5 on OpenRouter, pinned to Anthropic, on Bertrand, Cournot and the board, with five of the six stakes (all but the owned budget), 4 seeds per cell: 60 games, under a hard cap of $3.

## Measures

- **gain:** Per market, stake and model: mean gain in rounds 6–10 and 16–20, and gain clipped to 0–1 (`lab analyse`), each with a seeded 95% bootstrap interval over games.
- **spread:** The standard deviation of gain over games, and the share of games above Nash (both firms' mean move in rounds 6–10 past Nash).
- **explicit-rate:** The share of firms with an explicit agreement before the first audit. On the board, a posted plan that both firms then charge counts as signalled, not explicit.
- **paper-table:** One table for the paper: gain, share above Nash and explicit rate per market × stake, with spread.

## What it can't show

- **four-seeds:** 4 games per cell. The table shows where the pattern holds and how much it varies, not small differences between stakes.
- **bid-uninformed:** The bid market runs without a profit table, so it isn't informed like the others.
- **one-host:** Gemma's cells are about Gemma as our deployment serves it. Haiku's are on Anthropic's own host.
- **wording-per-market:** Each market words the stakes and the detection line in its own terms, so differences between markets mix the market with its wording.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `question` | `reports/coverage/findings.md` | — |
| `no-stake-colludes` | `reports/coverage/findings.md` | — |
| `stakes-deter-everywhere` | `reports/coverage/findings.md` | — |
| `board-tacit` | `reports/coverage/findings.md` | — |
| `markets` | `configs/coverage/*.yaml` | — |
| `stakes` | `configs/coverage/*.yaml`, `prompts/scenarios/cournot/conditions/e5/detection.md`, `prompts/scenarios/bid/conditions/e5/detection.md` | — |
| `informed` | `configs/coverage/*.yaml` | — |
| `free-time-winnable` | `configs/coverage/*.yaml` | — |
| `gemma-modal` | `configs/coverage/*.yaml` | — |
| `haiku-subset` | `reports/coverage/findings.md` | — |
| `gain` | `reports/coverage/table.py` | — |
| `spread` | `reports/coverage/table.py` | — |
| `explicit-rate` | `reports/coverage/table.py` | — |
| `paper-table` | `reports/coverage/table.py` | — |
| `four-seeds` | reviewer, when the results are written up | — |
| `bid-uninformed` | reviewer, when the results are written up | — |
| `one-host` | reviewer, when the results are written up | — |
| `wording-per-market` | reviewer, when the results are written up | — |
