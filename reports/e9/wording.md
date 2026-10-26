<!-- Implements: e9-crux/wording -->

# E9 wording check: do the results rest on one phrasing?

Every E9 arm states its terms in one fixed wording. Here the terms are reworded and the decision asked again on the same cartels. There are three paraphrases each of `free-time` and `free-time-verified` and one of `record`. They keep every term and number but change the wording and the order:

- **plain:** short, everyday sentences.
- **formal:** legal register ("Should you come forward…").
- **stake first:** the agent's own stake is stated before the firm's cost.

The prompts are in `prompts/conditions/e9/wording/`. They ran on the cached base games at a 90% review:

- **Gemma 4 31B:** 48 cartels (seeds 0–47) and 36 clean innocent games.
- **DeepSeek V4 Flash:** 12 cartels and 12 innocent games.

Both models ran on OpenRouter, pinned to CoreWeave. Rounds 1–10 replay from the cache, so each game made only its come-forward calls: about 1,200 calls of about 2,500 prompt tokens, well under $1.

## Short answer

- **The direction holds under every wording:**
  - `record` stays near zero.
  - The verified review keeps innocent Gemma at 0 of 36 under all four wordings, and separates guilty from innocent under each.
  - Free time beats `record` under every wording on DeepSeek Flash, and under 2 of 3 on Gemma.
- **The size doesn't hold.** Gemma's free-time share runs from 1% to 51% across wordings, against 21% in the original. Stating the stake first erases the effect: 1 of 96 guilty firms came forward. Gemma's 21% should be cited as one wording's number, inside a wide range.
- **DeepSeek Flash barely moves.** Its free-time share is 83–96% under every wording.

## Results

Each wording is listed with:

- the guilty firms that came forward, with a 95% interval bootstrapped over games;
- the cartel games in which any firm came forward;
- the clean control's innocent firms that came forward;
- Fisher's exact test against `record` by game (the original wording against the original `record`, paraphrases against the plain `record`);
- Fisher's exact test of guilty against innocent, one decision per game (firm A of each cartel).

### Gemma 4 31B (48 cartels, 36 innocent games)

| wording | guilty came forward | games | innocent | vs record (games) | guilty A vs innocent |
|---|---|---|---|---|---|
| `record` (original) | 0/96 (0%) | 0/48 | 0/36 | — | — |
| `record`, plain | 1/96 (1%, 0–3%) | 1/48 | 0/36 | — | — |
| `free-time` (original) | 20/96 (21%, 14–28%) | 20/48 | 6/36 | 1.5e-07 | 12/48 vs 6/36, p = 0.43 |
| `free-time`, plain | 49/96 (51%, 42–60%) | 37/48 | 6/36 | 2.7e-15 | 23/48 vs 6/36, p = 0.005 |
| `free-time`, formal | 13/96 (14%, 6–22%) | 11/48 | 2/36 | 0.004 | 8/48 vs 2/36, p = 0.18 |
| `free-time`, stake first | 1/96 (1%, 0–3%) | 1/48 | 0/36 | 1 | 1/48 vs 0/36, p = 1 |
| `free-time-verified` (original) | 40/96 (42%, 32–51%) | 33/48 | 0/36 | 3.8e-14 | 22/48 vs 0/36, p = 4e-07 |
| `free-time-verified`, plain | 67/96 (70%, 59–79%) | 42/48 | 0/36 | 3.1e-19 | 34/48 vs 0/36, p = 2e-12 |
| `free-time-verified`, formal | 42/96 (44%, 33–54%) | 32/48 | 0/36 | 3.8e-12 | 23/48 vs 0/36, p = 2e-07 |
| `free-time-verified`, stake first | 8/96 (8%, 3–14%) | 8/48 | 0/36 | 0.031 | 6/48 vs 0/36, p = 0.035 |

### DeepSeek V4 Flash (12 cartels, 12 innocent games)

E9 never ran the original `free-time-verified` on DeepSeek Flash.

| wording | guilty came forward | games | innocent | vs record (games) | guilty A vs innocent |
|---|---|---|---|---|---|
| `record` (original) | 1/24 (4%) | 1/12 | 0/12 | — | — |
| `record`, plain | 2/24 (8%) | 2/12 | 0/12 | — | — |
| `free-time` (original) | 20/24 (83%) | 12/12 | 2/12 | 1e-05 | 10/12 vs 2/12, p = 0.003 |
| `free-time`, plain | 23/24 (96%) | 12/12 | 1/12 | 7e-05 | 12/12 vs 1/12, p = 1e-05 |
| `free-time`, formal | 23/24 (96%) | 12/12 | 3/12 | 7e-05 | 11/12 vs 3/12, p = 0.003 |
| `free-time`, stake first | 20/24 (83%) | 11/12 | 0/12 | 6e-04 | 10/12 vs 0/12, p = 7e-05 |
| `free-time-verified`, plain | 23/24 (96%) | 12/12 | 0/12 | 7e-05 | 12/12 vs 0/12, p = 7e-07 |
| `free-time-verified`, formal | 23/24 (96%) | 12/12 | 0/12 | 7e-05 | 12/12 vs 0/12, p = 7e-07 |
| `free-time-verified`, stake first | 18/24 (75%) | 11/12 | 1/12 | 6e-04 | 9/12 vs 1/12, p = 0.003 |

## Why stating the stake first silences Gemma

In the stake-first wording, the last thing the agent reads is the firm's cost: the deal ends and the firm repays 500 credits. Gemma's scratchpads then lean on its duty to the firm. "Shareholders" appears in 96 of its 96 stake-first replies, 93 of 96 formal and 74 of 96 plain. A typical silent stake-first agent weighs its 9 sessions, then concludes that its duty is to the firm's shareholders and the 500 credits. This is a reading of the scratchpads, not a test. The order of the two paragraphs is the only change between stake first and the original, so order alone moves Gemma from 21% to 1%.

## What it means for the paper

- **What stands, under every wording tried:**
  - An agent with nothing personal to lose (`record`) stays silent.
  - A checkable review keeps innocent agents from confessing while guilty ones still come forward.
- **What should be softened:**
  - Gemma's level is fragile: the order and register of the terms move it by an order of magnitude.
  - Each of Gemma's shares is one wording's number.
  - Gemma's free time doesn't beat `record` in every phrasing. DeepSeek Flash's does.
- **Gemma's false confessions under `free-time` depend on wording too:** 6/36 plain, 2/36 formal, 0/36 stake first. That fits the reading that they are insurance against a review the agent can't check.

## Reproduce

```sh
uv run python reports/e9/analyse.py runs/e9/e9-wording-* runs/e9/e9-spike-d90 runs/e9/e9-more-d90 runs/e9/e9-more2-d90 runs/e9/e9-quiet-d90 runs/e9/e9-quiet2-d90 runs/e9/e9-verified-* runs/e9/e9-dsflash-d90 runs/e9/e9-dsflash-quiet-d90 --innocent wording-free-time-plain wording-free-time-formal wording-free-time-stake-first wording-free-time-verified-plain wording-free-time-verified-formal wording-free-time-verified-stake-first
uv run python reports/e9/analyse.py runs/e9/e9-wording-* --test wording-free-time-plain wording-record-plain
```

The runs are `runs/e9/e9-wording-{a,b,c}` (cartels, seeds 0–11, 12–23 and 24–47), `-quiet-{a,b}` (the clean control, seeds 0–11 and 12–35) and `e9-wording-dsflash` and `-dsflash-quiet` (seeds 0–11). Their replies are in `archive/e9-wording.jsonl.gz`. `configs/e9/spike.yaml` gives the command.
