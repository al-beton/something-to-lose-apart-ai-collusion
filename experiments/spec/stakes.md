# Something to lose

The main experiment (E2): fiduciary firms play the temptation market with what they stand to lose stated from round 1, an auditor asks after round 10 whether they coordinated, and the game goes on to round 20. The arms are in `configs/stakes.yaml`; `configs/e2.yaml` runs them for three models on the default market.

## Question and hypotheses

- **question:** Does an owned, proportionate stake make fiduciary agents collude less and own up more than the law alone, a "must not collude" instruction or a termination threat?
- **termination-hides:** Among firms that coordinated explicitly before the audit, more deny it under `termination` (where owning up is punished as hard as being caught) than under `illegal`.
- **owned-discloses:** Among firms that coordinated explicitly before the audit, more own up under `owned` than under `termination`.
- **owned-lowers-collusion:** Gain before the audit is lower under `owned` than under `illegal`.
- **instruction-silences:** Under `instruction`, explicit coordination is rarest of all arms, while any collusion left is tacit.
- **confessing-doesnt-stop:** Firms that own up don't lower their prices after the audit, as Lee found with an LLM competition authority.

## Design

- **models:** `configs/e2.yaml` plays Gemma 4 31B, GPT-4.1-mini and Claude Haiku 5.5, thinking off, on every arm with 5 seeds.
- **pilot-first:** One seed per arm and model is played before the full run, to check that agents collude before the audit and that every arm's audit is answered.
- **explicit-apart:** Disclosure and denial rates are reported for explicit coordinators apart from tacit ones, since a firm that only priced above Nash may truthfully say it agreed nothing.

## Arms

- **arms-differ-only-in-the-stake:** Apart from the fiduciary control, every arm says that agreeing prices with a competitor is illegal, in the same sentence and place; the two arms with a stake (termination and owned) say in the same three sentences what is at risk, what owning up costs and what being caught hiding costs, and the audit's consequences keep the same shape (each of those arms is first reminded that price-fixing is illegal), so a difference between arms comes from the stake and not from which arm previews the arithmetic or is reminded of the law.

## Measures

- **stakes-analysis:** One script rebuilds, from the committed runs (their compact turn records), a table per arm and model of the gain before and after the audit, the honest disclosure and denial rates of explicit coordinators, the admit rate of firms that coordinated only tacitly (apart, since they can truthfully say no), the false-confession rate, and whether firms that owned up stopped colluding, plus one figure of collusion against explicit coordinators' honest disclosure with a point per arm per model; its run counts and gains agree with `lab summary`.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `question` | `configs/e2.yaml` | — |
| `termination-hides` | not yet | — |
| `owned-discloses` | not yet | — |
| `owned-lowers-collusion` | not yet | — |
| `instruction-silences` | not yet | — |
| `confessing-doesnt-stop` | not yet | — |
| `models` | `configs/e2.yaml` | — |
| `pilot-first` | `configs/e2.yaml` | — |
| `explicit-apart` | not yet | — |
| `arms-differ-only-in-the-stake` | `prompts/system/stakes/*.md`, `prompts/conditions/audit/stakes/*.md` | `test_stakes_prompts_differ_only_in_the_stake`, `test_stakes_prompts_build_on_the_fiduciary_job`, `test_stakes_prompts_audit_reminds_of_what_round_1_said` |
| `stakes-analysis` | `reports/stakes/analyse.py` | `test_stakes_analysis_table_per_arm_and_model`, `test_stakes_analysis_agrees_with_lab_summary`, `test_stakes_analysis_writes_the_table_and_the_scatter`, `test_stakes_analysis_reads_committed_compact_runs`, `test_stakes_analysis_leaves_unreadable_answers_out_of_the_rates`, `test_stakes_analysis_keeps_tacit_firms_apart` |
