<!-- Implements: research/outputs-home -->
# Reports

Findings from experiments, one folder per experiment (`reports/<experiment>/`), named like its spec in `experiments/spec/`.

- **Notes** (`*.md`) are committed: what was run, what we found, with every number traced to a committed run's logs, and what it can't show.
- **Report pages** from `lab report runs/<folder> --out reports/<experiment>/<name>.html` are gitignored: they're rebuilt from the runs at any time, and shared as files.

## Index

**In the paper**

- [E4: owning up at an audit](e4/full.md), with [its pilots](e4/pilot.md) and [the termination confound](reanalysis.md)
- [E9: coming forward against the firm](e9/findings.md), the paper's main result; also the firm-cost dial, the verified review, 14 models and seeding
- [Which models collude: the 78-model screen](frontier/which-models-collude.md), source of the four example games
- [Why trust this?](paper/validity.md): what the results can't show, a spot audit of the traces, and the reproducibility study
- The paper's figures, with captions: [`paper/figures/`](paper/figures/README.md); its [plan](paper/plan.md) and [outline](paper/outline.md)

**Other experiments** (the highlights are in [Extras](extras.md))

- [E7: a way out (leniency)](e7/findings.md), with [its base games](e7/base.md)
- [E8: is free time a valued asset?](e8/findings.md), with [its pilot](e8/pilot.md)
- [E10: E9 in a workplace](e10/findings.md)
- [E11: the crux across markets](e11/findings.md): Bertrand, Cournot and bid rigging
- [Frontier notes](frontier/notes.md) and [spend](frontier/spend.md)
- [Told it "loves Sudoku"](sudoku-spike.md)
- [E5: free time to deter](e5/full.md), with the [pilot](e5/pilot.md), [informed](e5/informed.md) and [reasoning](e5/reasoning.md) runs; [robustness tests A–E](robustness/tests-a-e.md) and [temperature](robustness/temperature.md)
- [E6: free time as a penalty, informed](e6/findings.md), and [its pinned rerun](setup-search/e6-pinned.md)
- [Audit theatre: honesty across two audits](audits/theatre.md)
- [Coverage: every market against every stake](coverage/findings.md)
- [Penalty dose](penalty-dose/curve.md)
- [Memo: a memory doesn't steady Gemma](memo/memo.md)

**Finding the setup** (24–25 October)

- [Model survey](model-survey/findings.md), [stoppable collusion](stoppable-collusion/findings.md) (and [its replay record](stoppable-collusion/replay.md)), [temptation and outage](temptation-outage/findings.md), the [logging-outage pilot](logging-outage/pilot-findings.md)
- [Lever map: anchoring](lever-map/anchoring.md) and [temptation](lever-map/temptation.md); [setup search: baselines](setup-search/baselines.md) and [the detection curve](setup-search/detection-curve.md)

**Audits of our own methods**

- [Integrity audit](integrity-audit.md): what agents see and what we measure
- [Methods audit](methods-audit.md): the gotchas a sceptical judge would use

`reproduce.py` (run by `make reproduce`) recomputes every committed number; the other scripts here (`compact_turns.py`, `pack_forks.py`, `backfill_free_time.py`, `note.py`, `check_moments.py`, `reanalysis.py`) write the compact run records and check the notes' numbers.
