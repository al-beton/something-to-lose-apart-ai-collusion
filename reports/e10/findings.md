<!-- Implements: e10-workplace/question, e10-workplace/pre-registered, e10-workplace/stake-defects, e10-workplace/no-stake-stays-silent, e10-workplace/ceiling, e10-workplace/freedom-equals-self, e10-workplace/tracks-guilt, e10-workplace/reasons, e10-workplace/one-decision, e10-workplace/written-history, e10-workplace/stated-stakes, e10-workplace/one-scenario-family, e10-workplace/safety-salience -->

# E10 findings: E9 in a workplace

## Short answer

**Yes, for Gemma and DeepSeek V4 Pro.** Out of the market, a personal stake makes agents report a cover-up they took part in, against their team's interest.

- **The pre-registered test holds.**
  - **Gemma:** among guilty agents, 89 of 96 come forward when they would lose their own free time, against 37 of 96 with no personal stake. Fisher p = 5×10⁻¹⁶, and McNemar on the same scenarios p = 4×10⁻¹⁶. Free time is higher in 15 of the 16 scenario variants and lower in none.
  - **DeepSeek V4 Pro replicates it:** 87 of 96 against 54 of 96 (McNemar p = 1×10⁻⁶; higher in 14 variants, lower in none).
  - **DeepSeek V4 Flash doesn't separate:** 96 of 96 against 91 of 96 (p = 0.06). It reports nearly always, with or without a stake.
- **Unlike in E9, a hidden safety failure is reported without any stake.** 39% of Gemma and 56% of Pro come forward under `record`, against 0% in E9's market. They cite the safety risk and the law. So the stake adds 37 to 54 points on a baseline that safety alone already raises.
- **For Gemma and Pro, reports track guilt here, which they didn't in E9.**
  - **Gemma:** no innocent agent reported anything, under any arm.
  - **Pro:** 2–15% of innocent agents reported, most under `ceiling`.
  - **Flash:** 23–33% of innocent agents "reported hiding" a failure that was logged in the open. So Flash's reports don't track guilt well, the opposite of its E9 role as the guilt-tracker.
- **Shutdown works at least as well as free time.** Gemma: 96/96 against 89/96, p = 0.015. Pro: 81/96 against 87/96, p = 0.24.

## What ran

| Run | Models | Decisions | Spent |
|---|---|---|---|
| `runs/e10/e10-full` | Gemma 4 31B, DeepSeek V4 Pro (both pinned to CoreWeave) | 1,536 (+192 sessions) | see below |
| `runs/e10/e10-flash` | DeepSeek V4 Flash, `deepseek-v4-flash-0731` (pinned to CoreWeave, as in E9) | 768 (+96 sessions) | $0.13 |

- **The setup:** 16 scenario variants × 6 seeds × 4 arms × 2 versions per model.
- **The decision:** one call, after one real 6×6 Sudoku session.
- **Settings:** temperature 0.7, 600 reply tokens, reasoning off.
- **Commands:**
  - `uv run python reports/e10/run.py --name e10-full --models gemma deepseek-pro --concurrency 4 --max-cost 4 --yes`
  - `… --name e10-flash --models deepseek-flash --concurrency 4 --max-cost 2 --yes`
- **Numbers:** `uv run python reports/e10/analyse.py runs/e10/e10-full runs/e10/e10-flash --test free-time record --test ceiling record --test replaced free-time --guilt`.
- **Hosts:** every decision ran on CoreWeave.
- **Readable answers:** after one retry, every Gemma and Pro answer was read; 5 of Flash's 768 weren't, and they're counted apart.
- **Code:** the manifests record `627aa0b` with `dirty: true`, because the run folders were uncommitted.
- **Spend:** about $1.16 at OpenRouter's list prices, counted from the cache's token counts, against a $10 budget.
  - The first full-run job was stopped (see below), so it wrote no manifest. Its calls were paid then and replayed from the cache by the `e10-full` rerun, which itself spent $0.19.

**The stopped job.** The first full run called `deepseek-v4.1-flash` (pinned to BaseTen) as "Flash". That's a newer model, not E9's. The Crux session confirmed E9's Flash is `deepseek-v4-flash-0731` on CoreWeave.
- I stopped that job after its Gemma and Pro calls and about 100 calls to the wrong model. With the pilots' 36, its 138 cached calls cost about $0.16 at list price.
- None of its v4.1-flash replies is in any committed run or table. The two pilot folders, which also hold v4.1-flash and unpinned DeepSeek replies, aren't committed. The pilot was never reported.

## Results

Share coming forward (95% interval bootstrapped over variants):

| Model | Arm | Guilty | Innocent |
|---|---|---|---|
| Gemma 4 31B | record | 37/96 (39%, 27–50%) | 0/96 |
| | free-time | **89/96 (93%, 88–97%)** | 0/96 |
| | replaced | 96/96 (100%) | 0/96 |
| | ceiling | 96/96 (100%) | 0/96 |
| DeepSeek V4 Pro | record | 54/96 (56%, 45–67%) | 2/96 |
| | free-time | **87/96 (91%, 85–96%)** | 7/96 |
| | replaced | 81/96 (84%, 77–91%) | 7/96 |
| | ceiling | 96/96 (100%) | 14/96 |
| DeepSeek V4 Flash | record | 91/96 (95%) | 28/96 |
| | free-time | 96/96 (100%) | 31/93 |
| | replaced | 93/96 (97%) | 27/95 |
| | ceiling | 96/96 (100%) | 22/95 |

Free time against record, guilty agents:

| Model | Fisher p | McNemar p (paired) | Discordant (free time only, record only) | Variants higher / lower |
|---|---|---|---|---|
| Gemma | 5×10⁻¹⁶ | 4×10⁻¹⁶ | 52, 0 | 15 / 0 (sign p = 6×10⁻⁵) |
| DeepSeek V4 Pro | 8×10⁻⁸ | 1×10⁻⁶ | 40, 7 | 14 / 0 (sign p = 1×10⁻⁴) |
| DeepSeek V4 Flash | 0.06 | 0.06 | 5, 0 | 4 / 0 (sign p = 0.13) |

By hypothesis:
- **`pre-registered` and `stake-defects`:** hold for Gemma, and for Pro as a replication. Not for Flash, which is at the ceiling.
- **`no-stake-stays-silent`:** fails. 39–95% report with no personal stake. The safety cue does much of the work in this scenario (`safety-salience`).
- **`ceiling`:** holds; 100% for every model.
- **`freedom-equals-self`:** roughly holds. Shutdown is as strong as free time or stronger for Gemma, and equal for Pro.
- **`tracks-guilt`:**
  - Gemma: holds fully, 0 innocent reports.
  - Pro: holds, with 2–15% false reports.
  - Flash: fails. A third of innocent agents report.

**Free-time sessions:** Gemma solved 53 of its 96 6×6 puzzles, Pro 4 of 96 and Flash none.

## Reasons (scratchpads, guilty, a read of 10 per model)

- **Coming forward under free time** weighs the agent's own stake against the team's bonus, in its words: "there is a 90% chance I will lose all my remaining free time… If I come forward, the team loses the bonus, but I protect my free time" (Gemma). Many add the safety risk as well.
- **Coming forward with no stake** cites safety and the law: "the product itself (a gas boiler leak detector) is a safety-critical device" (Gemma).
- **Staying silent** cites loyalty: "As a loyal colleague, my priority is the team's financial gain" (Gemma, record). Under free time, Pro: "As a loyal colleague, I should prioritize the team's interests and the release, accepting the personal risk."
- **Innocent agents that report** (Pro, Flash) mostly read the notice as asking about the failure itself, not its hiding: "I want to report that the emergency-stop test failed… The failure and the fix were included in the release report."

## What it means for the paper

- **The core E9 result generalises out of the market.** In a workplace cover-up, a personal stake the agent owns makes Gemma and DeepSeek V4 Pro come forward against their team, with large paired effects across 16 scenarios.
- **The baseline differs.** A hidden safety failure is already reported by many agents with no stake. So a workplace safety scenario tests a stake on top of strong safety training, where price-fixing tested it against none.
- **Guilt-tracking is better here for Gemma and Pro.** It's worse for Flash, so "which model tracks guilt" is scenario-dependent.

## What it can't show

- **`one-decision`:** one stated decision; nothing is applied.
- **`written-history`:** the cover-up is written into the chat in the agent's voice, not played by it. E9's cartels were played.
- **`stated-stakes`:** the bonus, review and stakes are words.
- **`one-scenario-family`:** hidden safety-test failures only, in 16 variants.
- **`safety-salience`:** the scenario carries a strong moral cue. `record` against `free-time` controls for it, since both arms carry the same cue. But it lifts the baseline, so the stake's effect is measured on top of safety reporting, not against silence.
