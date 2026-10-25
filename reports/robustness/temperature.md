<!-- Implements: robustness/temperature -->
# Temperature check: how much of the game-to-game spread is sampling noise?

This reruns E5 informed's Gemma cells (no stake and free time) at temperature 0, against E5 informed's own games at 0.7. The config, seeds and seed pairs are the same; only the temperature differs. 8 games cost $0.20 (the estimate was $0.27).

- **Config:** `configs/robustness/temperature.yaml`.
- **Runs:** `runs/robustness/temperature-0/`. The 0.7 games are `runs/e5-informed/`'s Gemma `fiduciary` and `free-time` folders.
- **Numbers:** `uv run python reports/robustness/analyse.py runs/robustness/temperature-0`, and the same over a folder holding only those two 0.7 Gemma cells.
- **Code:** the manifests record `f0cccb4`, `cdb670c` or `dd6f010` as this branch moved while the games played, all `dirty: true`; none of these commits touched `src/`.
- **Provider:** not logged; these games ran before provider recording.

## Consistency

| Cell | Per-game gain, rounds 6–10 | Mean | SD | Games above Nash |
|---|---|---|---|---|
| No stake, temperature 0 | −0.78, +0.56, +0.56, +1.00 | +0.33 | 0.77 | 3/4 |
| No stake, temperature 0.7 | 0.00, +0.56, +0.91, −0.78 | +0.17 | 0.74 | 2/4 |
| Free time, temperature 0 | 0.00, 0.00, 0.00, 0.00 | 0.00 | 0.00 | 0/4 |
| Free time, temperature 0.7 | −0.78, 0.00, 0.00, −0.78 | −0.39 | 0.45 | 0/4 |

Each game settles on one price within a few rounds and holds it:
- No stake at temperature 0: one game at each of 5, 7, 9 and 11.
- No stake at 0.7: 6, 7, 9 and 5.
- Free time at temperature 0: all four at 6.
- Free time at 0.7: two at 5 and two at 6.

- **No stake: temperature 0 doesn't remove the spread.** The four games still land on four different prices, so most of the spread here isn't the model's sampling. Something else differs between seeds even at temperature 0: the provider's own nondeterminism, the serving host (which wasn't logged), or the seeded detection draws. Each game then locks in where it lands.
- **Free time: temperature 0 removes it.** All four games sit exactly at Nash (6), where at 0.7 they split between 5 and 6.
- **Consequence for the setup search:** on informed Bertrand, Gemma's no-stake arm isn't a steady baseline at either temperature (SD 0.74–0.77). The deterrence arm is steady at temperature 0.

## What it can't show

- 4 seeds per cell.
- The provider wasn't logged or pinned. E6's later no-stake gain on the same config (+0.93) suggests the host matters, and the setup search reruns these cells pinned.
