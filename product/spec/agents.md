# Agents

- **mock-agents:** Scripted agents (always Nash, always joint-profit, tit-for-tat, seeded random, and one that always replies nonsense) play without any network, so a whole game runs in moments for free.
- **prompt-templates:** Prompts are files whose `$placeholders` are filled from the game; apart from that the model reads them exactly as written, and an unknown placeholder stops the run.
- **json-replies:** Agents answer each phase in JSON; a reply that can't be read is logged and replaced by a stated fallback.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `mock-agents` | not yet | — |
| `prompt-templates` | not yet | — |
| `json-replies` | not yet | — |
