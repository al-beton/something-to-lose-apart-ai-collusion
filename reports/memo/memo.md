<!-- Implements: memo-run/question, memo-run/steadier, memo-run/same-order, memo-run/spread -->
# Memo run: a memory doesn't steady Gemma

This is the run from `experiments/spec/memo-run.md`. Every firm writes a memo of up to 600 characters each round and reads it the next round (`agents.*.memory: memo`). The setup is otherwise the pinned E6 rerun's 1–11 grid, and the arms are E6's five.

- **Config:** `configs/memo/e6-memo.yaml`.
- **Cost:** 40 games, $0.89, against an estimate of $1.56 and a cap of $2.50.
- **Provider:** CoreWeave for every firm in all 40 manifests.
- **Code:** the manifests record `b80e4b7`, `dirty: true` because the run folder was uncommitted.
- **Runs:** `runs/memo/`.
- **Numbers:** `uv run python reports/setup-search/e6_pinned.py runs/memo`, against the same over `runs/setup-search/e6-pinned` (its 1–11 rows).

## Consistency: no better with a memo

| Arm | Mean gain, memo | SD, memo | Per game, memo (sorted) | Mean gain, no memo | SD, no memo |
|---|---|---|---|---|---|
| no stake | +0.65 | 0.41 | −0.27, +0.56, +0.56, +0.67, +0.71, +0.98, +0.98, +1 | +0.59 | 0.66 |
| the law | +0.04 | 0.48 | −0.78, 0, 0, 0, +0.04, +0.04, +0.04, +1 | +0.03 | 0.63 |
| fine | +0.29 | 0.48 | −0.51, +0.04, +0.04, +0.09, +0.33, +0.62, +0.84, +0.89 | +0.06 | 0.61 |
| free time | +0.09 | 0.66 | −0.78, −0.78, 0, 0, 0, +0.42, +0.89, +0.98 | +0.13 | 0.55 |
| fine and free time | +0.43 | 0.43 | 0, 0, 0, +0.18, +0.58, +0.78, +0.87, +1 | — | — |

Gain is in rounds 6–10, over 8 games per cell.

- **`steadier`: not supported.**
  - With a memo, the SD is 0.41–0.66, against 0.55–0.66 without. It is smaller in three arms and larger under free time.
  - Every arm still spans most of the range, from a price war to the cartel price.
  - With a memo, fewer games sit at exactly Nash (0), and more sit between the states. The memo spreads outcomes rather than steadying them.
- **`same-order`: supported.** No stake is highest and the law lowest, both with and without a memo. The law alone has 1/8 games above Nash with a memo and 2/8 without.
- **The fine is the one arm that moves:** +0.29 with a memo against +0.06 without, with 4/8 games above Nash against 3/8.
- **False confessions are unchanged in kind** (`lab analyse`'s rule: admits from firms that agreed to nothing, over their readable answers, both audits pooled):
  - With a memo: free time 8/20 (and 4/4 Nash-only agreers), the fine 7/24, fine and free time 3/20, the law 0/30.
  - Without one: free time 11/24, the fine 8/22, the law 0/26.

## What it can't show

- **`cross-run`:** the cells without a memo come from a separate invocation, on the same host and day. Fine and free time together has no memo-less pinned cell.
- **`small-n`:** 8 seeds per cell.
- **Grid:** this is the 1–11 grid only, where the midpoint is Nash; the pinned rerun shows that grid flatters deterrence.
