# Research

- **hypothesis-first:** Each experiment states its question, arms and metrics before it runs.
- **results-from-logs:** Every number we report comes from a committed run's logs, never from memory or a console.
- **honest-limits:** Write-ups say plainly what an experiment can't show.
- **outputs-home:** Experiment specs live in `experiments/spec/`, and reports and findings notes in `reports/`, where notes are committed and generated pages are not.
- **every-run-committed:** Every experiment run is committed under `runs/<experiment>/` with its config, summary, manifest and compact turn record; scratch smoke runs are the only exception.
- **moments-indexed:** Notable moments are indexed in `reports/moments.yaml`, each with a label, the model, the run, round, phase and firm, the field quoted and a short quote found in that turn, so the paper can quote them with their source.
- **references:** Sources we build on or compare against are listed in `experiments/references.md`, each with why it matters to the lab and how far we checked it.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `hypothesis-first` | `.agents/skills/review-pr/SKILL.md` | — |
| `results-from-logs` | `.agents/skills/review-pr/SKILL.md` | — |
| `honest-limits` | `.agents/skills/review-pr/SKILL.md` | — |
| `outputs-home` | `.agents/skills/team/SKILL.md`, `reports/README.md`, `.gitignore` | — |
| `every-run-committed` | `runs/**`, `.agents/skills/review-pr/SKILL.md`, `reports/stakes/rescore.py` | — |
| `moments-indexed` | `reports/moments.yaml` | — |
| `references` | `experiments/references.md` | — |
