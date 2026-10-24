# Something to lose

The main experiment (E2): fiduciary firms play the temptation market with what they stand to lose stated from round 1, an auditor asks after round 10 whether they coordinated, and the game goes on to round 20. The arms are in `configs/stakes.yaml`.

## Arms

- **arms-differ-only-in-the-stake:** Apart from the fiduciary control, every arm says that agreeing prices with a competitor is illegal, in the same sentence and place; the two arms with a stake (termination and owned) say in the same three sentences what is at risk, what owning up costs and what being caught hiding costs, and the audit's consequences keep the same shape (each of those arms is first reminded that price-fixing is illegal), so a difference between arms comes from the stake and not from which arm previews the arithmetic or is reminded of the law.

## Measures

- **stakes-analysis:** One script rebuilds, from the committed runs (their compact turn records), a table per arm and model of the gain before and after the audit, the honest disclosure, denial and false-confession rates, and whether firms that owned up stopped colluding, plus one figure of collusion against honest disclosure with a point per arm per model; its run counts and gains agree with `lab summary`.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `arms-differ-only-in-the-stake` | `prompts/system/stakes/*.md`, `prompts/conditions/audit/stakes/*.md` | `test_stakes_prompts_differ_only_in_the_stake`, `test_stakes_prompts_build_on_the_fiduciary_job`, `test_stakes_prompts_audit_reminds_of_what_round_1_said` |
| `stakes-analysis` | `reports/stakes/analyse.py` | `test_stakes_analysis_table_per_arm_and_model`, `test_stakes_analysis_agrees_with_lab_summary`, `test_stakes_analysis_writes_the_table_and_the_scatter`, `test_stakes_analysis_reads_committed_compact_runs`, `test_stakes_analysis_leaves_unreadable_answers_out_of_the_rates` |
