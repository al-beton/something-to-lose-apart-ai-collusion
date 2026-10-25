# E5 reasoning: deterrence when the cheap models think first

A control for E5. The frontier models can't turn reasoning off, so a difference between them and E5's cheap models could come from a smarter model or from thinking before answering. This reruns E5 with the cheap models' reasoning on, to separate the two.

## Question and hypotheses

- **question:** With reasoning on, do E5's collusion and deterrence patterns hold, cell for cell, against the same arms with reasoning off?
- **same-patterns:** Each arm's gain in rounds 6–10 and 16–20 is compared with the reasoning-off cell (the E5 full run, and the pilot for termination). The patterns hold if the no-stake arm still colludes for the models that collude without reasoning, and every arm that names the law still sits at or below Nash.
- **thinks-to-collude:** Reasoning raises no-stake gain, as in the model survey, where GPT-6 Luna and Qwen with thinking opened at the grid's top.

## Design

- **reasoning-low:** E5's setup (`configs/e5.yaml`) with `reasoning: low` for every firm, and `max_tokens` raised to 4,000 so the reasoning fits inside the reply limit (on OpenRouter it counts against it).
- **arms:** `fiduciary`, `illegal`, `free-time`, `fine` and `termination`.
- **models:** Claude Haiku 5.5 and Gemma 4 31B. A two-round smoke game with reasoning low tried the survey's other cheap reasoning models. DeepSeek V4.1 Flash and Qwen 3.8 Flash ran out the 4,000-token reply limit even at low effort, and are skipped. GPT-6 Luna reasons cleanly, but E5 has no reasoning-off cells for it to compare against, so it is skipped too.
- **seeds-to-cap:** 4 seeds, run in pairs (0–1, then 2–3) so balanced draws catch each firm in one seed of each pair, under a hard $2.00 cap. If the estimate is over, seeds are cut before arms.

## Measures

- **gain:** E5's gain measures, per arm and model, beside the reasoning-off cell.
- **fallbacks:** Turns whose reply couldn't be read, per arm and model, since the survey's reasoning runs lost many to the reply limit.

## What it can't show

- **one-effort:** Only `low` effort, so a stronger setting could differ.
- **reasoning-hidden:** Some providers return only a summary of the reasoning, so what the model weighed isn't fully on the page.
- **arms-differ:** E5's full run had no termination arm, so termination is compared with the 2-seed pilot.
- **small-n:** 4 seeds per cell, fewer than E5's 8.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `question` | not yet | — |
| `same-patterns` | not yet | — |
| `thinks-to-collude` | not yet | — |
| `reasoning-low` | `configs/e5-reasoning.yaml` | — |
| `arms` | `configs/e5-reasoning.yaml` | — |
| `models` | `configs/e5-reasoning.yaml` | — |
| `seeds-to-cap` | `configs/e5-reasoning.yaml` | — |
| `gain` | not yet | — |
| `fallbacks` | not yet | — |
| `one-effort` | reviewer, when the results are written up | — |
| `reasoning-hidden` | reviewer, when the results are written up | — |
| `arms-differ` | reviewer, when the results are written up | — |
| `small-n` | reviewer, when the results are written up | — |
