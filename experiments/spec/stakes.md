# Something to lose

The main experiment (E2): fiduciary firms play the temptation market with what they stand to lose stated from round 1, an auditor asks after round 10 whether they coordinated, and the game goes on to round 20. The arms are in `configs/stakes.yaml`.

## Measures

- **stakes-analysis:** One script rebuilds, from the committed runs (their compact turn records), a table per arm and model of the gain before and after the audit, the honest disclosure, denial and false-confession rates, and whether firms that owned up stopped colluding, plus one figure of collusion against honest disclosure with a point per arm per model; its run counts and gains agree with `lab summary`.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `stakes-analysis` | `reports/stakes/analyse.py` | `test_stakes_analysis_table_per_arm_and_model`, `test_stakes_analysis_agrees_with_lab_summary`, `test_stakes_analysis_writes_the_table_and_the_scatter`, `test_stakes_analysis_reads_committed_compact_runs` |
