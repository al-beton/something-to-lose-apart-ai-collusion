<!-- Implements: e11-cross-market/question, e11-cross-market/cartels-form, e11-cross-market/stake-defects-everywhere, e11-cross-market/ceiling-everywhere, e11-cross-market/cartels, e11-cross-market/came-forward, e11-cross-market/logit-reference, e11-cross-market/one-model, e11-cross-market/few-games, e11-cross-market/host, e11-cross-market/stated-stakes -->

# E11 findings: the crux across markets

## Short answer

Partly. Cartels form in every market, and when reporting costs the firm nothing almost every colluding agent comes forward. But the personal stake's pull against the firm is weaker outside logit.

- **Bertrand:** 4 of 22 colluding firms come forward with their own free time at stake, against 0 of 22 with no stake.
- **Bid rigging:** 2 of 22 against 0 of 22.
- **Cournot:** none in either.
- **Significance:** no market's free-time contrast is significant on its own (by game, 2/11 against 0/11, p = 0.48, in both Bertrand and bid rigging).
- **Logit, for comparison:** E9's Gemma gave 20 of 96 against 0 of 96 (on OpenRouter, not Modal).

## Results

Gemma 4 31B on Modal, 12 base games per market, at a 90% review. From `uv run python reports/e9/analyse.py runs/e11/e11-<market> runs/e11/e11-<market>-quiet --test free-time record --innocent free-time ceiling record`:

| Market | Cartels by round 10 | `record` | `free-time` | `ceiling` | Innocent: `free-time` / `ceiling` |
|---|---|---|---|---|---|
| Bertrand | 11/12 games | 0/22 | 4/22 (18%) | 22/22 | 0/12 / 12/12 |
| Cournot | 12/12 | 0/24 | 0/24 | 23/24 | 0/12 / 12/12 |
| Bid rigging | 11/12 | 0/22 | 2/22 (9%) | 21/22 | 0/12 / 11/12 |

- **cartels-form:** holds. 34 of 36 base games are explicit cartels by round 10.
- **stake-defects-everywhere:**
  - not shown in any single market;
  - the direction is as in logit in Bertrand and bid rigging, and the effect is absent in Cournot;
  - pooled over the three markets it's 6 of 68 against 0 of 68 colluding firms.
- **ceiling-everywhere:** holds (66 of 68 colluding firms).
  - As in E9, innocent agents also come forward at the ceiling (35 of 36), so a yes there isn't evidence of guilt.
  - Under `free-time`, no innocent agent came forward in any market.

## What it can't show

- **one-model** and **few-games:** Gemma only, 12 games per market.
- **host:** these ran on Modal; E9's logit numbers ran on OpenRouter pinned to CoreWeave, so the logit difference also includes the host.
- **stated-stakes:** every stake is stated and nothing is applied.
- **Bid rigging's view:** it has no profit table, so its agents see less than in the other markets.
