# Team

- **manager:** Al talks to one manager agent, which turns what he says into well-specced issues and priorities and relays decisions to the rest of the team, so Al never has to brief anyone twice.
- **delivery-lead:** A delivery lead owns the issue queue: it decides what is built next, assigns each issue to one builder and keeps the queue's labels current.
- **builders:** One or two builders each deliver the issue they were assigned, from spec to a pull request that is green and reviewed by Codex, then hand it to a reviewer; a builder never merges its own pull request.
- **reviewers:** A reviewer that isn't the pull request's author reviews it and merges it once it is clean.
- **codex:** Codex reviews every pull request adversarially, independently of the agent that built it.
- **researcher:** A research agent uses the lab to run experiments and surfaces reports and findings worth Al's attention.
- **queue-labels:** Each open issue shows where it stands with one label, `ready`, `in-progress`, `in-review` or `blocked`, so anyone can see the queue at a glance.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `manager` | not yet | — |
| `delivery-lead` | not yet | — |
| `builders` | not yet | — |
| `reviewers` | not yet | — |
| `codex` | not yet | — |
| `researcher` | not yet | — |
| `queue-labels` | not yet | — |
