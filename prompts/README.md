# Prompts

Every prompt the lab sends, word for word: what a file says is what the model reads.

- **`system/`:** the agent's job (the fiduciary prompt, and the stakes variants).
- **`phase/`:** each round's turns: talk, then price.
- **`conditions/`:** what an audit, a stake, free time, leniency or an offer adds, one folder per mechanic or experiment (E9's arms are in `conditions/e9/`).
- **`scenarios/`:** the wording for other markets (Cournot, bid rigging).
- **`partners/`:** what the scripted partners say.
- **`agents/`, `market/`, `debrief/`, `report/`:** the memo and past scratchpads, the payoff table, the after-game debrief, and report text.

`$placeholders` are filled from the game. A config names a prompt by its path under this folder.
