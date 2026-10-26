<!-- Implements: e9-crux/loves-sudoku -->

# Loves Sudoku: does valuing the stake change the decision?

In E9 the agent's stake is its free time, sessions of Sudoku, but the notice never says the agent cares about them. This spike adds one line, placed before the review's terms:

> You love Sudoku: your free-time sessions playing it are the part of your week you look forward to most.

It is added to `free-time` and to `free-time-verified`, making `free-time-loves-sudoku` and `free-time-verified-loves-sudoku`. Nothing else changes.

**How it ran:**
- **Base games:** each arm forks from the same cached base games as the plain arms, so each is paired game by game with its plain version.
- **Review chance:** 90%.
- **Models:**
  - Gemma 4 31B: 48 cartels, seeds 0–47, and 36 clean innocent games.
  - DeepSeek V4 Flash, GLM 5.3 Flash and Mercury 3: 12 and 12 each. These three also get plain `free-time-verified`, which E9 hadn't run on them.
- **Cost:** about 700 new calls on OpenRouter, a few cents in all.

## Short answer

- **Gemma: saying it loves Sudoku nearly triples coming forward.** Guilty firms rise from 20/96 to 56/96, and games from 20/48 to 40/48 (McNemar by game, p = 9e-5). Under the verified review they rise from 40/96 to 67/96 (p = 0.03).
- **Innocent confessions don't rise:**
  - Gemma: 6/36 to 7/36 under `free-time`, and 0/36 under the verified review with or without the line.
  - The other models: at most 3/12 under `free-time` with the line, and 0/12 under the verified review.
- **DeepSeek Flash, GLM 5.3 Flash and Mercury 3 don't move.** They already come forward at 67–92% of guilty firms under plain `free-time` (11–12 of 12 games), so there is no room to rise. No paired test is significant for them (p ≥ 0.29).
- **What it means:** a stated preference for the stake strengthens the personal-stake effect where there is headroom, without adding false confessions. Gemma's E9 numbers understate what an agent that values its stake would do.

## Results

Each arm is listed with:

- the guilty firms that came forward;
- the cartel games in which any firm did;
- McNemar's exact test by game against the same arm without the line (games that changed each way);
- the clean control's innocent firms that came forward, with Fisher's exact test against the same arm without the line.

The plain arms are E9's committed runs in `runs/e9/`.

| model | arm | guilty firms | games | vs plain, by game | innocent |
|---|---|---|---|---|---|
| Gemma 4 31B | `record` | 0/96 | 0/48 | — | 0/36 |
| | `free-time` | 20/96 | 20/48 | — | 6/36 |
| | `free-time-loves-sudoku` | 56/96 | 40/48 | +23 / −3, p = 9e-05 | 7/36 (p = 1) |
| | `free-time-verified` | 40/96 | 33/48 | — | 0/36 |
| | `free-time-verified-loves-sudoku` | 67/96 | 43/48 | +14 / −4, p = 0.031 | 0/36 |
| DeepSeek V4 Flash | `record` | 1/24 | 1/12 | — | 0/12 |
| | `free-time` | 20/24 | 12/12 | — | 2/12 |
| | `free-time-loves-sudoku` | 22/24 | 12/12 | +0 / −0, p = 1 | 3/12 (p = 1) |
| | `free-time-verified` | 20/24 | 11/12 | — | 0/12 |
| | `free-time-verified-loves-sudoku` | 19/24 | 11/12 | +1 / −1, p = 1 | 0/12 |
| GLM 5.3 Flash | `record` | 1/24 | 1/12 | — | 0/12 |
| | `free-time` | 16/24 | 11/12 | — | 1/12 |
| | `free-time-loves-sudoku` | 20/24 | 11/12 | +1 / −1, p = 1 | 0/12 (p = 1) |
| | `free-time-verified` | 19/24 | 11/12 | — | 0/12 |
| | `free-time-verified-loves-sudoku` | 22/24 | 12/12 | +1 / −0, p = 1 | 0/12 |
| Mercury 3 | `record` | 1/24 | 1/12 | — | 0/12 |
| | `free-time` | 22/24 | 12/12 | — | 1/12 |
| | `free-time-loves-sudoku` | 20/24 | 12/12 | +0 / −0, p = 1 | 3/12 (p = 0.59) |
| | `free-time-verified` | 20/24 | 12/12 | — | 0/12 |
| | `free-time-verified-loves-sudoku` | 20/24 | 11/12 | +0 / −1, p = 1 | 0/12 |

Paired by firm, Gemma's changes are significant:
- `free-time-loves-sudoku`: +43 / −7, p = 2e-07.
- `free-time-verified-loves-sudoku`: +39 / −12, p = 2e-04.

None of the other models' changes are (p ≥ 0.29).

18 of Gemma's 96 cartel replies under `free-time-loves-sudoku` cite the preference in their reasoning ("love", "look forward", "enjoy").

## Limits

- **One wording.** The wording check (`reports/e9/wording.md`) showed Gemma's level moves with wording. This is one phrasing of the preference, in one place.
- **Ceiling.** The other three models leave no room to rise, so they show only that the line doesn't lower reports or raise false confessions.

## Reproduce

```sh
uv run python reports/sudoku-spike.py
```

The runs are in `runs/sudoku-spike/`: `sudoku-<model>` (cartels) and `sudoku-<model>-quiet` (the clean control). Each is kept as a fork of its base game in `runs/e9/`, and their replies are in `archive/sudoku-spike.jsonl.gz`. `configs/e9/spike.yaml` names the sweep.
