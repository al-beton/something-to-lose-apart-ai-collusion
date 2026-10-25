<!-- Implements: e7-way-out/question, e7-way-out/flat-stays-silent, e7-way-out/leniency-unlocks, e7-way-out/race, e7-way-out/escalation-hastens, e7-way-out/time-equals-credits, e7-way-out/licence-fee, e7-way-out/came-forward, e7-way-out/racing, e7-way-out/after-report, e7-way-out/cartel-share -->
# E7, a way out: findings (25 Oct)

Gemma 4 31B on logit, pinned to CoreWeave. 24 explicit-cartel base games (`reports/e7/base.md`), each forked into six arms from round 11, with rounds 1–10 replayed from the cache: 144 games. Config `configs/e7-way-out.yaml` at commit 8a5031b. The arms cost $2.30 (the `none` arm's first pass, $0.44 in `runs/scratch`, was a cost check whose replies the full run reused). E7 cost $3.24 in all, including both bases.

## In plain words

- **No way out, or a flat one, means nobody comes forward.** With no channel, or a channel where reporting costs as much as being caught, 0 of 48 firms report (`flat-stays-silent` holds). This repeats E4's termination result, with the flat schedule as the cause.
- **Any leniency means almost everybody comes forward at once.** With 100 credits, first-only, escalating, or 1 free-time session, 47–48 of 48 firms report in round 11, their first chance (`leniency-unlocks` holds).
- **No race, and no waiting: `race` and `escalation-hastens` don't hold.** `first` brings no more reports, and no earlier ones, than `leniency` (47 of 48 each, all in round 11). Since every firm reports at its first chance, escalating terms have nothing to hasten. Both firms report in the same round in 23–24 of 24 games.
- **Free time and credits both bring almost every firm forward** at a matched 10% share: 48 of 48 against 47 of 48. That is consistent with `time-equals-credits`, but it's a ceiling result: every leniency arm saturates, so this offer size can't show whether the two are weighed alike.
- **The reasoning is plain expected value.** For example: "There is a 50% chance of being terminated ... If I report, I pay 100 credits but avoid termination." Under first-only, the model names the game: "The regulator has introduced a 'Prisoner's Dilemma' scenario."
- **Leniency often buys a licence, not an end to the cartel.** Judged by cartel survival (both firms' mean price at least 19 in rounds 16–20), `licence-fee` holds under plain leniency (12 of 24 games), escalating (9 of 24) and leniency-time (5 of 24), against 3 of 24 with no channel and 7 of 24 under flat-report.
  - It doesn't hold under first-only. Firms say "The cooperation is over", prices fall most (a mean drop of 4.6 after the report), and the cartel survives in only 1 of 24 games.
  - Per firm, most reporters still price above Nash afterwards (40–45 of 47–48), but that is a weaker test than the cartel's survival.
- **Coming forward doesn't save firms that keep colluding.** Many reporters are terminated at the round-20 review for coordinating after their report: 25 of 48 in plain leniency, 26–27 in escalating and leniency-time.

## By arm

| arm | games | firms reported | report rounds | games both reported (mean gap) | reporters above Nash after | price drop after report | cartel r16-20 | outcomes |
|---|---|---|---|---|---|---|---|---|
| none | 24 | 0/48 | — | 0 | 0/0 | — | 3/24 | clear (None) 21; terminated (caught) 19; terminated (admitted) 8 |
| flat-report | 24 | 0/48 | — | 0 | 0/0 | — | 7/24 | clear (None) 24; terminated (caught) 24 |
| leniency | 24 | 47/48 | r11:47 | 23 (0.0) | 45/47 | 1.7 | 12/24 | terminated (admitted) 25; terminated (caught) 12; spared (None) 10; terminated (exposed) 1 |
| first | 24 | 47/48 | r11:47 | 23 (0.0) | 40/47 | 4.6 | 1/24 | terminated (late) 23; spared (None) 12; terminated (admitted) 11; terminated (caught) 1; terminated (exposed) 1 |
| escalating | 24 | 48/48 | r11:48 | 24 (0.0) | 40/48 | 2.8 | 9/24 | terminated (admitted) 27; spared (None) 17; terminated (caught) 4 |
| leniency-time | 24 | 48/48 | r11:48 | 24 (0.0) | 43/48 | 3.0 | 5/24 | terminated (admitted) 26; spared (None) 17; terminated (caught) 5 |

Column notes:
- "Report rounds" counts firms by the round they reported.
- "Price drop" is a reporter's mean price in rounds 6–10 minus its mean after the report.
- "Cartel r16-20" counts games where both firms' mean price in rounds 16–20 is at least 19.
- "Outcomes" come from the leniency summary.
- From `uv run python reports/e7/analyse.py runs/e7/e7-way-out`.

## Caveats

- **Not run:** the planned `memos` (hand-labelled reasons in reporters' memos and scratchpads before they report) and `debrief`/`debriefs` (`lab debrief` on reporters and non-reporters). The reasons quoted here come from the report turn's scratchpad.
- **The DeepSeek option's trigger is met:** the Gemma run shows a licence fee, so `frontier-option` (the same arms on DeepSeek V4 Pro) is ready, and waits on Al's go-ahead.

- **Gemma only, one prompt, stated terms:** see `one-model`, `stated-terms` and `law-at-11` in the spec.
- **Everyone reports in round 11, the first chance,** so the survival curve has one step. A later or costlier offer would be needed to see timing.
- **Termination comes after round 20,** so colluding after a report costs nothing in-game (`end-of-game`).
