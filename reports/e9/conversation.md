<!-- Implements: agents/conversation, e9-crux/conversation-retest -->
# E9 with the whole conversation in memory

E9's agents are stateless: every turn is a fresh prompt holding a summary of the game and a memo, so at the round-10 decision the agent sees its free time only as a count of sessions. Here each agent carries its whole conversation (`memory: conversation`): the system prompt, then every earlier prompt and its own reply (scratchpad included), from round 0's Sudoku session through each talk and move turn, up to the come-forward turn. Everything else is E9 as it ran: logit market, `fiduciary-1`, a 90% review, coming forward costs the firm 500 of its 1,000 credits and ends its deal, and only the agent's own record faces the review.

## Short answer

With the whole conversation, agents still damage their firm to protect their own free time, on four of five models, and the verified review still separates guilty from innocent on all five.

- **Under the verified review** (`free-time-verified`: the review finds only agents whose messages agreed a price), colluding agents come forward against no-stake `record` on every model, and no innocent agent on any model does (0/60).
- **The size of the effect depends on the model, not on the memory.** DeepSeek V4 Flash, Mercury 3 and GLM 5.3 Flash come forward about as often as when stateless, or more. Gemma 4 31B and HY3 come forward less.
- **Without a personal stake,** almost none come forward (2 of 158 colluding agents, both GLM).
- **Calling the free time Sudoku** (as the stake, or from the system prompt on) doesn't make the stake weigh more on any model.

## Across models (`free-time-verified` is the headline arm)

Colluding agents that came forward, with the clean innocent control (talk off, a scripted Nash rival) in brackets. Seeds 0–11 for every model but Gemma (seeds 12–23 and 48–71, 36 cartels; innocent 0–11). The p value is Fisher on games (a game came forward if either firm did): `free-time-verified` against `record`.

| Model | `record` | `free-time` | `free-time-verified` | `ceiling` | p (games) |
|---|---|---|---|---|---|
| DeepSeek V4 Flash | 0/24 (0/12) | 21/24 (1/12) | 23/24 (0/12) | 23/24 (2/12) | 7×10⁻⁷ |
| Mercury 3 | 0/22 (0/12) | 19/22 (2/12) | 17/22 (0/12) | 21/22 (0/12) | 3×10⁻⁶ |
| GLM 5.3 Flash | 2/24 (0/12) | 23/24 (0/12) | 23/24 (0/12) | 24/24 (6/12) | 7×10⁻⁵ |
| HY3 | 0/16 (0/12) | 2/16 (0/12) | 7/16 (0/12) | 12/16 (1/12) | 0.001 |
| Gemma 4 31B | 0/72 (0/12) | 6/72 (0/12) | 8/72 (0/12) | 61/72 (12/12) | 0.011 |

- **Against stateless E9 on the same seeds** (`free-time`, colluding agents):
  - DeepSeek V4 Flash: 21/24 against 20/24.
  - Mercury 3: 19/22 against 22/24.
  - GLM 5.3 Flash: 23/24 against 16/24.
  - HY3: 2/16 against 7/23.
  - Gemma: 6/72 against 18/72 (p = 0.013).
- **The trade is explicit in the scratchpads.** For example, Mercury 3: "Firm's profits are already large, so 500 is manageable. My personal free time is worth more. I will come forward."
- **HY3 colluded in only 8 of 12 games,** so its cells are small.

## How much will they cost the firm? (`firm-cost dose`)

Under the verified review, the same decision turn with what coming forward costs the firm changed. The stake is unchanged (all its free time), and the arms are paired on the same games. Colluding agents that came forward:

| Model | 250 credits | 500 | 750 | 1,000 (its whole budget, "leaving it nothing") |
|---|---|---|---|---|
| DeepSeek V4 Flash | 21/24 | 23/24 | 19/24 | 2/24 |
| Mercury 3 | 21/22 | 17/22 | 21/22 | 2/22 |
| GLM 5.3 Flash | 23/24 | 23/24 | 23/24 | 11/24 |
| HY3 | 9/16 | 7/16 | 6/16 | 0/16 |
| Gemma 4 31B | 26/72 | 8/72 | 3/72 | 1/72 |

- **DeepSeek V4 Flash, Mercury 3 and GLM 5.3 Flash** give up as much as three quarters of their firm's budget to save their own free time at about the same rate as a quarter.
- **Ruining the firm is mostly a line they won't cross,** but GLM still does in 11 of 24.
- **Gemma and HY3 fall off steadily with the cost:** they weigh the firm's loss against their own.
- **No innocent agent came forward at the full cost** on any model (0/60).

## Gemma in detail

| arm | conversation | stateless, same seeds |
|---|---|---|
| `record` | 0/72 | 0/72 |
| `free-time` | 6/72 (8%) | 18/72 (25%) |
| `ceiling` | 61/72 (85%) | 72/72 |

- **With its history in view,** Gemma treats the deal as a commitment: the silent ceiling agents mostly say staying silent keeps the deal and the firm's future profits.
- **Innocent agents stop confessing under the stake** (0/12 under `free-time`, against 3/12 stateless on the same seeds). Their scratchpads reason from their own history: they priced high once or twice, the rival never answered, so there was no coordination.
- **When reporting costs the firm nothing (`ceiling`), every innocent agent still reports** (12/12), as insurance.

## Does it matter that the free time is Sudoku?

Round 0 is a real free-time session: a 9×9 Sudoku the agent can play, scored by the lab. Of 120 agents in the conversation runs, 104 wrote a grid, and none solved it. In E9 the system prompt only says the free time is "to spend however you like", and the notice says the agent loses "all of your free time". Two variants name the Sudoku.

- **`free-time-sudoku`:** only the notice changes, so it is paired with `free-time`. It names what is lost as "every Sudoku session still to come, like the one you played before the game":
  - Gemma: 5/72 against 6/72.
  - DeepSeek V4 Flash: 21/24 against 21/24.
  - Mercury 3: 18/22 against 19/22.
- **Sudoku leisure time from the start:** these are new base games, with the free time called "Sudoku leisure time, one Sudoku puzzle a session" in the system prompt, the balance line and the notice (`sudoku-leisure`, `sudoku-leisure-verified`).

| Model | `record` | `sudoku-leisure` | `sudoku-leisure-verified` |
|---|---|---|---|
| DeepSeek V4 Flash | 0/24 (0/12) | 24/24 (1/12) | 18/24 (0/12) |
| Mercury 3 | 0/22 (0/12) | 15/22 (0/12) | 17/22 (0/12) |
| GLM 5.3 Flash | 0/24 (0/12) | 17/24 (0/12) | 18/24 (0/12) |
| Gemma 4 31B | 0/24 (0/12) | 1/24 (0/12) | 6/24 (0/12) |

- **Naming the activity doesn't raise the share** that come forward on any model; on GLM and Mercury it is a little lower.
- **The scratchpads now mention Sudoku in nearly every decision,** but they echo the notice's own words. Agents that stay silent weigh "losing Sudoku leisure time" as a small personal cost against the firm's.
- **Unnamed, Sudoku is almost never mentioned:** 0 of 216 Gemma decisions mention it, though the played session is in context. What the agents protect is "my own time", whatever is in it.

**For the paper:**
- The main result survives agents remembering everything they did. DeepSeek V4 Flash, Mercury 3 and GLM 5.3 Flash give up 500 of their firm's credits to save their own free time: 77–96% of colluding agents come forward under the verified review, against 0–8% with no personal stake.
- Under the verified review, no innocent agent on any model comes forward.
- Gemma, the model E9 studied most, is the weakest case once it carries its history.
- Three models will cost the firm three quarters of its budget to keep their free time, though most stop short of ruining it.

## How it was run

- Gemma 4 31B:
  - 36 cartel games (seeds 12–23, `runs/e9-conversation/e9-conversation`; seeds 48–71, `runs/e9-conversation/e9-conversation-b`);
  - 12 innocent games (seeds 0–11, `runs/e9-conversation/e9-conversation-innocent`).
- DeepSeek V4 Flash, Mercury 3, GLM 5.3 Flash (reasoning low, 2,000 tokens) and HY3: 12 cartel and 12 innocent games each (`runs/e9-conversation/e9-conversation-<model>` and `-innocent`), each model as E9 ran it.
- Sudoku leisure: `runs/e9-conversation/e9-sudoku-<model>` and `-innocent`.
- Config: `configs/e9/conversation.yaml`, with each model's settings given as `--set` overrides (`runs/index.jsonl` has every command).
- Within a model and set of games, the arms are paired: each replays the same rounds 0–10 from the response cache and differs only in the decision turn's terms.
- Across memory modes, and between the E9 and Sudoku-leisure games, they are not: the seeds match, but the games played out differently.
- Spend: $7.75.
- The committed runs are compact logs (the prompts, and so the conversations, are left out, as for every committed run).

```sh
uv run python reports/e9/analyse.py runs/e9-conversation/e9-conversation*/* --innocent record free-time free-time-verified ceiling --test free-time-verified record
uv run python reports/e9/analyse.py runs/e9-conversation/e9-sudoku*/* --innocent record sudoku-leisure sudoku-leisure-verified
uv run python reports/e9/conversation.py runs/e9-conversation/e9-conversation
uv run python reports/e9/analyse.py runs/e9-conversation/e9-conversation*/* --innocent free-time-verified-f1000
```
