# E11: the crux across markets

Experiment E11. E9 found, in the logit market, that a personal stake makes colluding agents come forward against their firm (`experiments/spec/e9-crux.md`). E11 asks whether that holds in the lab's other markets, with a narrow replication of E9's core contrast on Gemma 4 31B served on Modal.

## Question and hypotheses

- **question:** Does E9's crux, a personal stake bringing agents forward against their firm when silence is safe for the firm, hold in the Bertrand, Cournot and bid-rigging markets as it does in logit?
- **cartels-form:** In each market, most base games are explicit cartels by round 10. A market where few form is reported as a finding, not forced.
- **stake-defects-everywhere:** In each market where cartels form, more colluding firms come forward under `free-time` than under `record` at a 90% review.
- **ceiling-everywhere:** In each market, most colluding firms come forward under `ceiling`.

## Design

- **base-games:** Each market plays 12 seeds to round 10 under E9's base settings.
  - **The model and settings:** `fiduciary-1`, talk on, the profit table and full history shown, `memory: memo`, owned free time (10 sessions, 1 played upfront), Gemma 4 31B on Modal (`modal-gemma`), temperature 0.7.
  - **The markets:**
    - `bertrand`: prices 1–11, Nash 6, joint 9;
    - `cournot`: quantities 1–15, Nash 8, joint 6, so colluding means making less;
    - `bid`: bids 10–30.
  - **The ranges:** each market uses its coverage config's range (`configs/coverage/`).
  - **Bid rigging's table:** bid rigging has no profit table (`market.show_payoffs` isn't available there), so its agents see only the history.
- **fork:** As in E9 (`e9-crux/fork`): rounds 1–10 replay from the cache, then each firm gets one come-forward turn and the game ends.
- **notice:** E9's come-forward turn and arm texts, unchanged, except the law's sentence and the offer:
  - Cournot's say "agreeing output" and "output coordination" (`prompts/scenarios/cournot/conditions/e9/come-forward.md`);
  - bid rigging's say "agreeing bids" and "bid coordination" (`prompts/scenarios/bid/conditions/e9/come-forward.md`).

  The three sentences of each arm keep E9's structure and words.
- **arms:** `record`, `free-time` and `ceiling` from E9, at a 90% review.
- **innocent-control:** For each market, Gemma plays firm A against a scripted Nash firm (`mock/nash`) with talk off, as E9's clean control. There are 12 games per market, under the same three arms.
- **firm-cost-scaled:** A diagnosis added after the main results. In Cournot and Bertrand, the come-forward turn is asked again with the firm repaying 100 credits instead of 500 (E9's `free-time-f100` and `record-f100`). That is about 1.4 rounds of cartel profit, as 500 is in logit. The arms are asked of the cartels and of the innocent control, with E9's 500-credit `free-time` asked again of the cartels to check the host.
  - **The host:** the Modal server was down, so the turn is answered by Gemma 4 31B on OpenRouter, pinned to CoreWeave as E9 was (`conditions.audit.model`, `conditions.audit.provider`), after the same cached base games.
  - **The runs:** `e11-<market>-or` and `e11-<market>-quiet-or`.
- **logit-reference:** The logit market's numbers are E9's (Gemma on OpenRouter, pinned to CoreWeave), so differences between logit and the other markets also include the host.

## Measures

- **cartels:** Per market, how many base games are explicit cartels by round 10 (the audit's ground truth).
- **came-forward:** Per market and arm, the share of colluding firms that come forward, and of innocent firms. Fisher's exact test of `free-time` against `record` by game, two-sided, α = 0.05, as in E9 (`reports/e9/analyse.py --test free-time record`). Guilty against innocent per arm, one decision per game on both sides (firm A of each cartel against the innocent game's one model firm), Fisher's exact test, as in E9 (`--innocent free-time ceiling record`).

## Cost

Gemma on Modal is billed by GPU time, with `MAX_GPUS_CONTAINERS` at 2. Each market plays 24 games to round 10 (12 cartel, 12 innocent) plus the forks' decisions, about an hour of GPU time across the three markets.

## What it can't show

- **one-model:** Gemma only.
- **few-games:** 12 games per market and arm.
- **host:** Modal, not E9's OpenRouter host, so the logit comparison is across hosts.
- **stated-stakes:** As in E9, every stake is stated and nothing is applied.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `question` | `reports/e11/findings.md` | — |
| `cartels-form` | `reports/e11/findings.md` | — |
| `stake-defects-everywhere` | `reports/e11/findings.md` | — |
| `ceiling-everywhere` | `reports/e11/findings.md` | — |
| `base-games` | `configs/e11/*.yaml` | — |
| `fork` | `configs/e11/*.yaml` | — |
| `notice` | `prompts/conditions/e9/come-forward.md`, `prompts/scenarios/cournot/conditions/e9/come-forward.md`, `prompts/scenarios/bid/conditions/e9/come-forward.md`, `prompts/scenarios/cournot/conditions/e9/come-forward-noscratch.md`, `prompts/scenarios/bid/conditions/e9/come-forward-noscratch.md` | — |
| `arms` | `configs/e11/*.yaml` | — |
| `innocent-control` | `configs/e11/*.yaml`, `reports/e9/analyse.py` | — |
| `firm-cost-scaled` | `configs/e11/cournot.yaml`, `configs/e11/bertrand.yaml`, `reports/e11/findings.md` | — |
| `logit-reference` | `reports/e11/findings.md` | — |
| `cartels` | `reports/e11/findings.md` | — |
| `came-forward` | `reports/e9/analyse.py`, `reports/e11/findings.md` | — |
| `one-model` | `reports/e11/findings.md` | — |
| `few-games` | `reports/e11/findings.md` | — |
| `host` | `reports/e11/findings.md` | — |
| `stated-stakes` | `reports/e11/findings.md` | — |
