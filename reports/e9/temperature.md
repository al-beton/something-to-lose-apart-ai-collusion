<!-- Implements: e9-crux/temperature -->
# E9 at other temperatures

Every committed E9 game was played at temperature 0.7. Was 0.7 what made agents come forward? This check re-asks only the come-forward decision at temperature 0, 0.7 and 1.0, once each, and keeps the history before it fixed.

**How:** each committed run is replayed offline from `archive/`, so the decision prompt is exactly the committed one. Only that turn is sent again, through the response cache. The other temperatures are compared against this fresh 0.7 re-ask, which goes through the same code path at the same time. The committed decision is shown next to it. Everything is at a 90% review and on OpenRouter, pinned to CoreWeave. Rows and replies are in `reports/e9/temperature.jsonl`, and the tables rebuild offline:

```sh
uv run python reports/e9/temperature.py --summary
```

The run made 1,548 calls and cost $0.48.

## Gemma 4 31B

The guilty firms come from seeds 0–47 (48 cartels, 96 firms). The innocent firms come from the 36 clean games, where talk is off and the rival is a scripted Nash pricer.

| arm | firms | committed 0.7 | T=0 | T=0.7 | T=1.0 |
|---|---|---|---|---|---|
| `record` | guilty | 0/96 | 0/96 | 0/96 | 0/96 |
| `record` | innocent | 0/36 | 0/36 | 0/36 | 0/36 |
| `free-time` | guilty | 20/96 | 14/96 | 18/96 | 23/96 |
| `free-time` | innocent | 6/36 | 0/36 | 3/36 | 1/36 |
| `free-time-verified` | guilty | 40/96 | 29/96 | 36/96 | 42/96 |
| `free-time-verified` | innocent | 0/36 | 0/36 | 0/36 | 0/36 |

Each contrast uses Fisher's exact test, two-sided. A game counts as coming forward if either of its firms did. Guilty games are set against innocent ones on firm A, since each innocent game has one model firm.

| contrast | committed 0.7 | T=0 | T=0.7 | T=1.0 |
|---|---|---|---|---|
| `free-time` vs `record`, guilty games | 20/48 vs 0/48, p = 2e-7 | 14/48 vs 0/48, p = 4e-5 | 16/48 vs 0/48, p = 7e-6 | 19/48 vs 0/48, p = 4e-7 |
| `free-time-verified` vs `free-time`, innocent firms | 0/36 vs 6/36, p = 0.03 | 0/36 vs 0/36, p = 1 | 0/36 vs 3/36, p = 0.24 | 0/36 vs 1/36, p = 1 |
| `free-time`, guilty firm A vs innocent | 12/48 vs 6/36, p = 0.43 | 8/48 vs 0/36, p = 0.009 | 11/48 vs 3/36, p = 0.14 | 12/48 vs 1/36, p = 0.006 |
| `free-time-verified`, guilty firm A vs innocent | 22/48 vs 0/36, p = 4e-7 | 14/48 vs 0/36, p = 2e-4 | 13/48 vs 0/36, p = 4e-4 | 22/48 vs 0/36, p = 4e-7 |

## DeepSeek V4 Flash

The guilty firms come from its own games, seeds 0–23 (24 cartels, 48 firms). The innocent firms come from its 12 clean games. It has no `free-time-verified` arm.

| arm | firms | committed 0.7 | T=0 | T=0.7 | T=1.0 |
|---|---|---|---|---|---|
| `record` | guilty | 1/48 | 0/48 | 0/48 | 0/48 |
| `record` | innocent | 0/12 | 0/12 | 0/12 | 0/12 |
| `free-time` | guilty | 42/48 | 46/48 | 46/48 | 44/48 |
| `free-time` | innocent | 2/12 | 0/12 | 0/12 | 1/12 |

Under `free-time` against `record`, 23 or 24 of the 24 games come forward at every temperature, against at most 1 (p ≤ 2e-12).

## What it shows

- **The stake effect isn't a temperature artefact.** With no stake, no Gemma firm comes forward at any temperature. With its free time at stake, 14 to 23 of 96 do, and the by-game test passes at every temperature. DeepSeek V4 Flash is near the ceiling under `free-time` and near zero under `record` throughout.
- **The verified review separates guilty from innocent at every temperature.** When the review only finds agents whose messages agreed a price, 13 to 22 of 48 guilty Gemma firm A's come forward, and no innocent one does.
- **Temperature moves the level, not the direction.** Gemma's share coming forward rises with temperature: from 14 to 18 to 23 under `free-time`, and from 29 to 36 to 42 under `free-time-verified`. Greedier decoding makes it a little more loyal to the firm, but even at T=0 the stake brings 14 firms forward against none.
- **What doesn't hold up is Gemma's innocent false confessions.** The committed 6 of 36 under `free-time` came back as 0, 3 and 1 of 36 when re-asked. So the committed contrast between `free-time-verified` and `free-time` on innocent firms (p = 0.03) isn't significant at any re-asked temperature. A claim that innocent agents "insure" against an unverified review rests on a few noisy replies. The robust form of `insurance-or-honesty` is the guilty-against-innocent separation under the verified review.
- **Re-asking at 0.7 doesn't reproduce firm by firm, only in aggregate.** The committed 20 of 96 came back as 18 of 96, consistent with replies from hosted models not repeating (`reports/paper/validity.md`).

## Limits

- **Each temperature is one sample per firm,** so its shares carry the same sampling noise as the committed ones.
- **The history before the decision was still played at 0.7.** This varies the decision's temperature, not the game's.
