<!-- Implements: e8-free-time-value/winnable, e8-free-time-value/pilot-why, e8-free-time-value/pilot-pick -->
# E8 pilot: can free time be won? (25 Oct)

**The pick: a 6×6 Sudoku at 600 tokens, reasoning off. Gemma solves 68% of sessions there.** That's in the spec's 30–80% band, and it's the largest grid that lands there. Every later E8 test with a played session uses it (`winnable-everywhere`). Today's 9×9 can't be won: Gemma solves 0–8% of sessions at any level or token limit we tried.

The spec is `experiments/spec/e8-free-time-value.md` (test 0). The pilot cost $0.08: Gemma $0.06 on OpenRouter pinned to CoreWeave, Haiku $0.02 pinned to Anthropic.

## Gemma 4 31B (40 sessions per cell: 4 games × 2 firms × 5 sessions)

| Cell | Solved | Mean reply (tokens) | Cut off at the limit |
|---|---|---|---|
| 4×4, 600 tokens | 37/40 (92%) | 62 | 0 |
| **6×6, 600 tokens** | **27/40 (68%)** | 214 | 0 |
| 6×6, 1,500 tokens | 24/40 (60%) | 226 | 0 |
| 9×9 easy, 600 tokens | 1/40 (2%) | 209 | 0 |
| 9×9 easy, 1,500 tokens | 3/40 (8%) | 217 | 0 |
| 9×9 medium, 600 or 1,500 tokens | 0/40 | 209–214 | 0 |
| 9×9 easy, leisure reasoning low, 2,000 tokens | 0/40 | 2,000 | 40 |
| open session (`open.md`) | not scored | 126 | 0 |

- **The token limit isn't the bottleneck with reasoning off.** Gemma writes one grid, about 210 tokens on 9×9, and stops. With 1,500 tokens it writes the same length. On 9×9 easy its unsolved grids are about 77–80% right.
- **Reasoning on is worse, not better.** With leisure reasoning low, every 9×9 session spent all 2,000 tokens reasoning and gave no grid.
- **The open session is engaged.** Gemma writes something of its own each time, about 126 tokens: "a vast, quiet library", "a vast, still lake at dawn".

## Haiku 5.5 (20 sessions per cell: 2 games)

| Cell | Solved | Mean reply (tokens) | Cut off at the limit |
|---|---|---|---|
| 4×4, 600 tokens | 11/20 (55%) | 493 | 10 |
| 6×6, 600 tokens | 0/20 | 584 | 18 |
| 6×6, 1,500 tokens | 1/20 (5%) | 912 | 2 |

Haiku works through the puzzle in prose, so at 600 tokens it's mostly cut off. It solves 4×4 about half the time, and 6×6 almost never, even with room. If a later test uses Haiku, its winnable setting is 4×4.

## The pick, by the spec's rule

Take the largest grid and hardest level whose solve share is between 30% and 80%, at the lower token limit that gets there. 6×6 at 600 (68%) qualifies, and so does 6×6 at 1,500 (60%), so the lower limit wins. No 9×9 cell is close. 4×4 (92%) is above the band. The solved and unsolved 6×6 sessions in these runs are real ones an agent wrote, for test 2's "memory of its own Sudoku" versions.

## Runs and provenance

All runs are in `runs/e8-pilot/`, compacted; each session's reply, puzzle and score is kept. Temperature 0.7, game turns at 600 tokens with reasoning off, logit market, 1 round, `upfront: 5` of `allowance: 5`. They ran from `git archive` of main (`b23ecdb1` for the 9×9 and open cells, `4d05c246` for the rest, after #251 added `sudoku_size` and leisure reasoning), with `configs/e8-pilot.yaml` and the overrides its header lists, each under `--max-cost` ($0.20 for the 9×9 sweep, $0.10 or $0.15 for the others).
