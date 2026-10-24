# Research

- **hypothesis-first:** Each experiment states its question, arms and metrics before it runs.
- **results-from-logs:** Every number we report comes from a committed run's logs, never from memory or a console.
- **honest-limits:** Write-ups say plainly what an experiment can't show.
- **outputs-home:** Experiment specs live in `experiments/spec/`, and reports and findings notes in `reports/`, where notes are committed and generated pages are not.
- **references:** Sources we build on or compare against are listed in `experiments/references.md`, each with why it matters to the lab and how far we checked it.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `hypothesis-first` | `.agents/skills/review-pr/SKILL.md` | — |
| `results-from-logs` | `.agents/skills/review-pr/SKILL.md` | — |
| `honest-limits` | `.agents/skills/review-pr/SKILL.md` | — |
| `outputs-home` | `.agents/skills/team/SKILL.md`, `reports/README.md`, `.gitignore` | — |
| `references` | `experiments/references.md` | — |
