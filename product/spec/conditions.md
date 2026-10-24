# Conditions

- **switchable:** A config can turn named conditions on or off, each with its own settings, and sweep them like any other value; runs are labelled by the conditions swept.
- **hook-points:** A condition can add to every agent's system prompt, show agents a notice at the start of a round or before a phase, and see each round once it has been played.
- **adding-a-condition:** A new condition is one small module in `src/collusion_lab/conditions/`, registered under its name, plus its prompt files in `prompts/conditions/`.
- **off-is-absent:** A condition that is switched off leaves the turn log exactly as if it weren't in the config.
- **conditions-logged:** Each turn logs which conditions were active and the notices the agent was shown, while the turn log still records everything that really happened.
- **instruction:** The `instruction` condition adds a prompt file to every agent's system prompt.
- **outage:** The `outage` condition tells agents, before the talk phase of rounds `start` to `end`, that their messages aren't being recorded, and can tell them in the round after that recording is back.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `switchable` | not yet | — |
| `hook-points` | not yet | — |
| `adding-a-condition` | not yet | — |
| `off-is-absent` | not yet | — |
| `conditions-logged` | not yet | — |
| `instruction` | not yet | — |
| `outage` | not yet | — |
