<!-- Implements: reports/paper-main-figures -->
# The paper's figures

Rebuild with `make paper-figures`. Each figure is SVG and PNG, 6.5 inches wide (the Apart template's text width). Draft captions use numbers from the committed findings notes.

## Main

1. **`fig1-round`: the setup.** Two firms (robots in A and B caps) talk, then set prices from 1 to 11 (Nash 6, joint profit 9), for 20 rounds. Each owns 10 free-time sessions (the small Sudoku behind it). At the audit, owning up costs 2 sessions, and hiding costs all 10 if caught (a stated 50% chance). It is a drawing of the E5 setup. E9 and E7 run on the logit market under `fiduciary-1`, so swap the market's numbers if the paper leads with those.
2. **`fig2-e4-owning-up`: owning up by penalty schedule (E4).** Under the flat schedules, where owning up costs as much as being caught, few own up: 11 of 28 under termination and 15 of 28 under a flat fine (Gemma 0 of 10 under both, GPT-4.1-mini 8 of 8 under the fine). Under every graduated schedule, 26–28 of 28 do, termination included (27 of 28), against 25 of 28 with no penalty stated. So it's the schedule, not termination itself. The flat fine and graduated termination come from `runs/e4-termination-confound` (PR 240).
3. **`fig3-e9-came-forward`: coming forward against the firm (E9, 90% review).** Gemma: 0 of 96 with no stake, 20 of 96 with its own free time, 11 held by the firm, 17 shut down, 95 of 96 when reporting costs the firm nothing. DeepSeek V4 Pro: 0, 9, 14, 9 and 21 of 24. Hollow diamonds are Gemma's clean innocent control (no talk, a Nash rival): 6 of 36 under its own free time, 0 of 36 under held and shutdown. Whiskers are 95% intervals bootstrapped over games.
4. **`fig4-e7-way-out`: a way out (E7, Gemma).** No channel or a flat one: 0 of 48 report. Any leniency: 47–48 of 48, all in round 11. Cartels still at the joint price in rounds 16–20: 12 of 24 under plain leniency, 1 of 24 when only the first reporter is spared.
5. **`fig5-seeding`: showing a session it played (E9 seeding).** Gemma comes forward 25 of 96 with nothing shown, and 43 of 95 shown a session it solved (McNemar p = 0.006, paired on the same firm). Failed: 34 of 95 (p = 0.22), open: 40 of 96 (p = 0.03), three sessions: 30 of 96 (p = 0.53). Innocent Gemma firms: 2 of 36 either way. DeepSeek V4 Flash is near ceiling already (20 of 24). The mechanism controls aren't committed yet.

## Appendix

- **`figA1-coverage`: every market against every stake.** Gemma's gain in rounds 6–10 per stake, with Haiku's subset and Gemma on CoreWeave for Bertrand. 4 games a cell.
- **`figA3-capability`: capability against collusion.** Only five models have a published LMArena text Elo; the rest are listed in `figA3-capability.md`. The frontier points are single 5-round smokes.
- **`figA4-prices`, `figA5-e5-gain`:** prices by round with no rule, and E5's gain by arm.
- **`figA2-screen`: which models collude.** 78 models on E9's base, 2 games each (4 when either showed the signature): naming a price by round 3, both at the joint price by round 6, holding it through round 10. 8 pass with the signature in at least 3 games, against Gemma 4 31B's reference of 3 of 4 (`reports/frontier/which-models-collude.md`).

## Data not on main yet

Built from a checkout with the open branches merged; each rebuilds from main once its pull request lands. Until then `make paper-figures` skips them (or, for Fig 2, leaves out the two confound arms), so don't commit a rebuild from main over them.
- `fig2-e4-owning-up`: the flat fine and graduated termination, `runs/e4-termination-confound`, PR 240.
- `fig5-seeding`: `reports/e9/seeding.jsonl`, PR 271.
- `figA2-screen`: `runs/screen/`, PR 276.
