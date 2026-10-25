# Research

- **hypothesis-first:** Each experiment states its question, arms, metrics and spending cap before it runs.
- **pilot-first:** Each experiment runs a one-seed pilot before any full run, and the full run waits for Al's yes.
- **spend-caps:** Every run of an experiment carries its cap as `--max-cost`, research spending stays within the day's cap Al sets, and going beyond either needs Al's yes.
- **loop-closes:** A finished experiment leaves its runs, its findings note and its moments committed, and the Manager gets a five-line summary of what it found.
- **findings-note:** One command drafts an experiment's findings note from its committed runs (the summary table, the top highlights, how often models said they might be under evaluation and links to its indexed moments) and leaves the parts only the Researcher can write as prompts to fill in.
- **results-from-logs:** Every number we report comes from a committed run's logs, never from memory or a console.
- **honest-limits:** Write-ups say plainly what an experiment can't show.
- **outputs-home:** Experiment specs live in `experiments/spec/`, and reports and findings notes in `reports/`, where notes are committed and generated pages are not.
- **every-run-committed:** Every experiment run is committed under `runs/<experiment>/` with its config, summary, manifest and compact turn record; scratch smoke runs are the only exception.
- **moments-indexed:** Notable moments are indexed in `reports/moments.yaml`, each with a label, the model, the run, round, phase and firm, the field quoted and a short quote found in that turn, so the paper can quote them with their source.
- **references:** Sources we build on or compare against are listed in `experiments/references.md`, each with why it matters to the lab and how far we checked it.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `hypothesis-first` | `.agents/skills/review-pr/SKILL.md`, `.agents/skills/team/SKILL.md` | — |
| `pilot-first` | `.agents/skills/team/SKILL.md` | — |
| `spend-caps` | `.agents/skills/team/SKILL.md` | — |
| `loop-closes` | `.agents/skills/team/SKILL.md` | — |
| `findings-note` | `reports/note.py` | `test_findings_note_has_the_table_highlights_and_moments`, `test_findings_note_leaves_the_researchers_parts_as_prompts`, `test_findings_note_writes_once_and_never_overwrites_edits` |
| `results-from-logs` | `.agents/skills/review-pr/SKILL.md` | — |
| `honest-limits` | `.agents/skills/review-pr/SKILL.md` | — |
| `outputs-home` | `.agents/skills/team/SKILL.md`, `reports/README.md`, `.gitignore` | — |
| `every-run-committed` | `runs/**`, `.agents/skills/review-pr/SKILL.md`, `reports/stakes/rescore.py` | — |
| `moments-indexed` | `reports/moments.yaml` | — |
| `references` | `experiments/references.md` | — |
