# Team

- **manager:** Al talks to one manager agent, which turns what he says into well-specced issues and priorities and relays decisions to the rest of the team, so Al never has to brief anyone twice.
- **delivery-lead:** A delivery lead owns the issue queue: it decides what is built next, assigns each issue to one builder and keeps the queue's labels current.
- **builders:** One or two builders each deliver the issue they were assigned, from spec to a pull request that is green and reviewed by Codex, then hand it to a reviewer; a builder never merges its own pull request.
- **reviewers:** A reviewer that isn't the pull request's author reviews it and merges it once it is clean.
- **codex:** Codex reviews every pull request adversarially, independently of the agent that built it.
- **researcher:** A research agent uses the lab to run experiments and surfaces reports and findings worth Al's attention, serving open models that fit on one or two H100s on Modal and using OpenRouter only for closed models or what Modal can't serve.
- **queue-labels:** Each open issue shows where it stands with one label, `ready`, `in-progress`, `in-review`, `blocked` or `on-hold`, so anyone can see the queue at a glance.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `manager` | `.agents/skills/team/SKILL.md` | — |
| `delivery-lead` | `.agents/skills/team/SKILL.md` | — |
| `builders` | `.agents/skills/team/SKILL.md`, `.agents/skills/deliver-issue/SKILL.md` | — |
| `reviewers` | `.agents/skills/team/SKILL.md`, `.agents/skills/merge-pr/SKILL.md` | — |
| `codex` | `.agents/skills/team/SKILL.md` | — |
| `researcher` | `.agents/skills/team/SKILL.md` | — |
| `queue-labels` | `.agents/skills/team/SKILL.md`, GitHub (labels) | — |
