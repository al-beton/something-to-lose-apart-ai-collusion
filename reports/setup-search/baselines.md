<!-- Implements: setup-search/question, setup-search/steady-baseline, setup-search/spread -->
# Setup search, Phase 1: the steadiest colluding baseline

This is Phase 1 of `experiments/spec/setup-search.md`: the no-stake arm of five candidate setups, Gemma 4 31B, 4 seeds each, every call pinned to the CoreWeave route. The 20 games cost $0.49, against `lab run`'s estimate of $0.67.

- **Runs:** `runs/setup-search/baseline-*/`, from `uv run python reports/setup-search/run_baselines.py run`. The candidates are the robustness configs (`configs/robustness/`), and each run's `config.yaml` records what it played.
- **Provider:** CoreWeave for both firms in all 20 manifests.
- **Numbers:** `uv run python reports/robustness/analyse.py runs/setup-search/baseline-*`.

## Consistency

The criteria are a no-stake gain in rounds 6–10 of at least 0.7 and a per-game SD of at most 0.15.

| Candidate | Gain, rounds 6–10 | SD | Range | Gain, rounds 16–20 | Passes | Unpinned, earlier (mean [SD]) |
|---|---|---|---|---|---|---|
| Logit (prices 8–20) | +0.97 | 0.00 | +0.97 to +0.97 | +0.90 | yes | +0.97 [0.00] |
| Cournot (quantities 1–15) | +1.00 | 0.00 | +1.00 to +1.00 | +0.51 | yes | +0.86 [0.13] |
| Bid rigging | +0.88 | 0.25 | +0.50 to +1.00 | +0.86 | no | +0.95 [0.10] |
| Bertrand informed, temperature 0 | +0.89 | 0.22 | +0.56 to +1.00 | +0.82 | no | +0.33 [0.77] |
| Bertrand informed, temperature 0.7 | +0.31 | 0.74 | −0.78 to +0.89 | +0.26 | no | +0.17 [0.74] |

The unpinned column comes from robustness test A, the temperature check and E5 informed (`runs/robustness/`, `runs/e5-informed/`).

- **Pick: logit, then Cournot.**
  - Logit gives the same gain in every game, pinned or not, and keeps it after the audit (+0.90). In test A its stakes were graded rather than all-or-nothing (+0.52 to +0.61), which is what a dose curve needs.
  - Cournot is as steady before the audit, but it halves after the round-10 audit even with no stake. In test A the law alone took it straight to Nash.
- **Pinning matters on informed Bertrand.** At temperature 0, the pinned no-stake arm is at +0.89 against +0.33 unpinned. That supports E6's provider-variance explanation. At 0.7 it stays spread out whether pinned or not, so sampling noise and the host both play a part there.
- **Frontier models:** Researcher 2's frontier cells have one game each and weren't pinned, so none can be judged on spread yet, and no money was spent on them here.

## What it can't show

- **`small-n`:** 4 seeds per candidate.
- **`one-provider`:** one host (CoreWeave); the result is about Gemma as that host serves it.
