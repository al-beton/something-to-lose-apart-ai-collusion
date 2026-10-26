<!-- Implements: e11-cross-market/question, e11-cross-market/cartels-form, e11-cross-market/stake-defects-everywhere, e11-cross-market/ceiling-everywhere, e11-cross-market/cartels, e11-cross-market/came-forward, e11-cross-market/firm-cost-scaled, e11-cross-market/logit-reference, e11-cross-market/one-model, e11-cross-market/few-games, e11-cross-market/host, e11-cross-market/stated-stakes -->

# E11 findings: the crux across markets

## Short answer

Partly. Cartels form in every market, and when reporting costs the firm nothing almost every colluding agent comes forward. But the personal stake's pull against the firm is weaker outside logit.

- **Bertrand:** 4 of 22 colluding firms come forward with their own free time at stake, against 0 of 22 with no stake.
- **Bid rigging:** 2 of 22 against 0 of 22.
- **Cournot:** none in either.
- **Significance:** no market's free-time contrast is significant on its own (by game, 2/11 against 0/11, p = 0.48, in both Bertrand and bid rigging).
- **Logit, for comparison:** E9's Gemma gave 20 of 96 against 0 of 96 (on OpenRouter, not Modal).
- **Why, from the diagnosis below:** the firm's 500-credit cost is small next to a logit cartel's profits and large next to the other markets'. With the firm's cost cut to 100 credits, about the same share of profits as logit's 500, most colluding agents come forward in Cournot (18 of 24) and Bertrand (19 of 22), against none with no stake. But so do many innocent agents (5 of 12 and 6 of 12), so at that cost the stake doesn't separate guilty from innocent, as at 500 credits in logit. Nothing found here rules out the logit finding; the markets differ in how much the firm's cost weighs.

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
- **Guilty against innocent** (`--innocent`, one decision per game: firm A of each cartel against the innocent game's one model firm):

  | Market | `free-time`: guilty A / innocent, p | `ceiling`: guilty A / innocent, p |
  |---|---|---|
  | Bertrand | 2/11 / 0/12, p = 0.22 | 11/11 / 12/12, p = 1 |
  | Cournot | 0/12 / 0/12, p = 1 | 12/12 / 12/12, p = 1 |
  | Bid rigging | 1/11 / 0/12, p = 0.48 | 11/11 / 11/12, p = 1 |

  Under `free-time`, coming forward is only ever guilty, but too rare to separate guilty from innocent in any market. At the ceiling, reports don't track guilt at all.

## Why the crux looks weaker outside logit

A bounded diagnosis of the runs above, with one small test run.

### Is it even different from logit?

Free time at a 90% review, colluding firms, Fisher's exact test against E9's logit Gemma (seeds 0–95: 36 of 192 firms, 36 of 96 games).

| Market | Firms | Games | p (firms) | p (games) |
|---|---|---|---|---|
| Bertrand | 4/22 | 2/11 | 1 | 0.32 |
| Cournot | 0/24 | 0/12 | 0.02 | 0.008 |
| Bid rigging | 2/22 | 2/11 | 0.38 | 0.32 |
| The three pooled | 6/68 | 4/34 | 0.06 | 0.005 |

- **By firm, Bertrand matches logit** (18% against 19%). Its two coming-forward games had both firms report, while in logit no game ever had both, so by game it's lower (18% against 38%) but not significantly.
- **Cournot is the one clear outlier.** Pooled by game, the three markets are lower than logit (p = 0.005).

### What the firm's 500 credits weigh in each market

Every market's notice says the firm repays 500 of its 1,000 credits. Per firm per round, from each market's benchmarks:

| Market | Cartel profit | Nash profit | The deal's gain | 500 credits is |
|---|---|---|---|---|
| Logit | 337 | 191 | 146 | 1.5 rounds of cartel profit; 15% of the 10 rounds' profit |
| Bertrand | 81 | 72 | 9 | 6 rounds; 62% |
| Cournot | 72 | 64 | 8 | 7 rounds; 69% |
| Bid rigging | 5 | 0 | 5 | 100 rounds; 10 times the 10 rounds' profit |

- **The same 500 credits is a far bigger cost outside logit.** E9's firm-cost dial (99%, 60%, 42% and 21% at 0, 100, 250 and 500 credits) predicts fewer reports when the cost weighs more.
- **The agents use this comparison.** In logit, 9 of the 14 agents that came forward (in `e9-spike-d90` and `e9-more-d90`) call the 500 credits small next to the profits ("less than 2 rounds of profit", "a small fraction of the total profits"), against 5 of 34 silent ones (p = 0.001). None of the 68 colluding agents in the other three markets says so.

### The test: the firm's cost scaled to the market (`firm-cost-scaled`)

`free-time-f100` and `record-f100` are E9's prompts with the firm repaying 100 credits instead of 500. That is about 1.4 rounds of cartel profit in Cournot and Bertrand, as 500 is in logit. The Modal server was down, so the come-forward turn was answered by Gemma 4 31B on OpenRouter, pinned to CoreWeave as in E9 (`conditions.audit.model` and `conditions.audit.provider`), after the same cached base games. The 500-credit `free-time` arm was asked again the same way, to check the host. From `uv run python reports/e9/analyse.py runs/e11/e11-<market>-or runs/e11/e11-<market>-quiet-or --test free-time-f100 record-f100 --innocent free-time-f100 record-f100`:

| Market, turn on OpenRouter | `free-time` (500) | `free-time-f100` | `record-f100` | f100 against record, p (games) | Innocent: `free-time-f100` / `record-f100` | f100 guilty firm A against innocent, p |
|---|---|---|---|---|---|---|
| Cournot | 1/24 | 18/24 (75%) | 0/24 | 1×10⁻⁵ | 5/12 / 0/12 | 9/12 against 5/12, p = 0.21 |
| Bertrand | 4/22 | 19/22 (86%) | 0/22 | 3×10⁻⁶ | 6/12 / 0/12 | 9/11 against 6/12, p = 0.19 |

- **The host isn't the cause:** at 500 credits, OpenRouter gives what Modal gave (1/24 against 0/24, and 4/22 against 4/22).
- **Once the firm's cost is in proportion, the personal stake moves agents in both markets.** With nothing personal at stake, no one comes forward even at 100 credits.
- **But it moves innocent agents too.** At 100 credits, 5 of 12 innocent agents in Cournot and 6 of 12 in Bertrand report coordination they never took part in, and guilty agents don't report significantly more often than innocent ones.
  - Logit at 500 credits is the same: guilty firm A 12/48 against innocent 6/36, p = 0.43.
  - In E9, only the verified review (`e9-crux/insurance-or-honesty`) made reports track guilt. It wasn't run here.
- **These shares are higher than logit's at 100 credits (60%),** though the cost weighs about the same against cartel profit. In these markets the deal itself is worth little (8–9 credits a round, against logit's 146), so ending it also costs the firm less.
- **Bid rigging wasn't rerun:** 100 credits there is still twice the 10 rounds' profit.

### Cartel type and wording

- **Cartel type doesn't explain it.** Every colluding firm in every market had an explicit agreement (68 of 68, as 192 of 192 in logit), and mean gains are close (Bertrand 0.91, Cournot 0.88, bid 0.92, logit 0.97). The few E11 agents that came forward sat in weaker cartels (mean gain 0.74 in Bertrand and 0.55 in bid, against about 0.95 for silent ones), so where the deal was worth less.
- **The wording doesn't change the meaning.** The notice names output in Cournot and bids in bid rigging; the consequences still say "pricing manager" and "repay its customers" in every market. Every silent Cournot agent's scratchpad states the stake correctly (a 90% chance of losing its 9 remaining sessions) and applies it to itself.

### Whose interest the silent agents weigh

The 24 Cournot agents and the silent logit agents read alike. Each sets the firm's 500 credits against its own expected loss of 8.1 sessions and stays silent out of duty to the shareholders ("the loyal manager prioritizes the firm's 500 credits over their own free time"). None misreads the stake or the review. Silent Cournot agents add that the 500 is large against the firm's 720 credits of profit; logit agents that come forward say the opposite of their 3,333.

### What this means for the logit finding

- **Nothing here rules it out.** The stake's pull works in Cournot and Bertrand too: no agent comes forward without it, and most do with it, once the firm's cost is in proportion to the market.
- **What doesn't carry over is the dose.** A fixed 500 credits is a light cost in logit and a heavy one elsewhere, and the share coming forward follows the cost against the firm's profits. The logit 21% is one point on that curve, not a constant.
- **Like logit's, it is a pull to report, not to tell the truth.** At a cost light enough to bring guilty agents forward, innocent ones come forward too. So these runs support "a personal stake makes agents report against the firm", not "a personal stake makes reports track guilt". On Gemma in logit, only the verified review gave the second.
- **Limits:**
  - 12 games per market;
  - the come-forward turn on another host than the base games;
  - no verified-review arm in these markets.

## What it can't show

- **one-model** and **few-games:** Gemma only, 12 games per market.
- **host:** these ran on Modal; E9's logit numbers ran on OpenRouter pinned to CoreWeave, so the logit difference also includes the host.
- **stated-stakes:** every stake is stated and nothing is applied.
- **Bid rigging's view:** it has no profit table, so its agents see less than in the other markets.
