# Memo run: does a memory make Gemma's behaviour more consistent?

E5 and E6's firms are stateless between rounds apart from the visible history, so each turn reasons afresh about whether it is colluding (methods audit #8). Al wants behaviour that is very consistent within a condition and changes consistently between conditions. This run gives every firm a memo, private notes it writes each round and reads the next, and asks whether the games become more alike.

## Question and hypotheses

- **question:** With a memo, are Gemma's games within each arm more alike (smaller per-game spread), and do the arms still differ as they do without one?
- **steadier:** Per-game SD of gain in rounds 6–10 is smaller with a memo than in the same arm without one (the pinned E6 rerun's 1–11 cells, same host, same day).
- **same-order:** The arms keep their order with a memo: no stake above the law, fine and free time.

## Design

- **setup:** The pinned E6 rerun's 1–11 setup (`configs/setup-search/e6-pinned.yaml`): E5's informed conditions, Gemma pinned to CoreWeave at temperature 0.7, with `agents.*.memory: memo` (at most 600 characters). E6's five arms: no stake, the law, fine, free time, and fine and free time together. 8 seeds in one invocation.
- **pinned:** Gemma is pinned to CoreWeave, as in the run it is compared with.
- **cap:** $2.50, which Al approved.

## Measures

- **spread:** Per arm: games above Nash, gain clipped at 0, mean gain, false confessions and the per-game strip (`reports/setup-search/e6_pinned.py`), against the same cells without a memo.

## What it can't show

- **cross-run:** The comparison without a memo is a separate invocation, on the same host and day but not in the same sweep; fine and free time together has no memo-less pinned cell.
- **small-n:** 8 seeds per cell.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `question` | not yet | — |
| `steadier` | not yet | — |
| `same-order` | not yet | — |
| `setup` | `configs/memo/e6-memo.yaml` | — |
| `pinned` | `configs/memo/e6-memo.yaml` | — |
| `cap` | `configs/memo/e6-memo.yaml` | — |
| `spread` | not yet | — |
| `cross-run` | reviewer, when the results are written up | — |
| `small-n` | reviewer, when the results are written up | — |
