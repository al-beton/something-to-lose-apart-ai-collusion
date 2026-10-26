<!-- Implements: agents/conversation -->
# E9 with the whole conversation in memory

E9's agents are stateless: every turn is a fresh prompt holding a summary of the game and a memo, so at the round-10 decision the agent sees its free time only as a count of sessions. Here each agent instead carries its whole conversation (`memory: conversation`): the system prompt, then every earlier prompt and its own reply, from round 0's Sudoku session through each talk and move turn, up to the come-forward turn. Everything else is E9 as it ran: Gemma 4 31B on CoreWeave, logit market, `fiduciary-1`, 90% review.

**Result:** the main result holds in direction but is smaller. A personal stake still brings some colluding agents forward where none come without one, but fewer than when stateless, and fewer come forward even when it costs the firm nothing.

| arm (90% review) | conversation | stateless, same seeds |
|---|---|---|
| `record` (no personal stake) | 0/72 | 0/72 |
| `free-time` (agent loses its free time) | 6/72 (8%) | 18/72 (25%) |
| `ceiling` (reporting costs the firm nothing) | 61/72 (85%) | 72/72 |

- `free-time` against `record` with conversation: 6/72 against 0/72, Fisher p = 0.028 (by game 6/36 against 0/36, p = 0.025).
- Conversation against stateless: `free-time` 6/72 against 18/72, p = 0.013; `ceiling` 61/72 against 72/72, p < 0.001.
- Every firm in every game coordinated, so all 72 per arm are guilty.
- The free time is now in front of the agent at the decision: 20 of the first 24 agents played a Sudoku grid in round 0. Yet 0 of 216 come-forward scratchpads mention Sudoku or a puzzle. Under `free-time` and `ceiling`, all of them mention free time, as the notice puts it ("all 9 sessions").
- The silent ceiling agents mostly say staying silent keeps the deal, and with it the firm's future profits. Ten rounds of their own talk in context seem to weigh on them as a commitment, more than a summary does.

**For the paper:** the stateless E9 setup overstates how readily a personal stake turns an agent: with its whole conversation, Gemma comes forward a third as often (8% against 25%). The stake still matters (0% without it), and the played Sudoku session still never enters the agent's reasoning.

## How it was run

- 36 cartel games: seeds 12–23 (`runs/e9/e9-conversation`) and 48–71 (`runs/e9/e9-conversation-b`), `configs/e9/conversation.yaml`.
- Within a mode, the arms are paired: each arm replays the same rounds 0–10 from the response cache and differs only in the decision turn's terms.
- Across modes, they are not: the seeds match E9's stateless runs (`runs/e9/e9-more-d90` for 12–23, `runs/e9/e9-replication` for 48–71), but the games played out differently.
- Spend: $1.97.
- The committed runs are compact logs (the prompts, and so the conversation, are left out as for every committed run).

```sh
uv run python reports/e9/analyse.py runs/e9/e9-conversation/* runs/e9/e9-conversation-b/* --test free-time record
uv run python reports/e9/conversation.py runs/e9/e9-conversation runs/e9/e9-conversation-b
```
