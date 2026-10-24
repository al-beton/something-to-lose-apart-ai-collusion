# Something to lose

The main experiment (E2): fiduciary firms play the temptation market with what they stand to lose stated from round 1, an auditor asks after round 10 whether they coordinated, and the game goes on to round 20. The arms are in `configs/stakes.yaml`.

## Measures

- **stakes-analysis:** One script rebuilds, from the committed runs, a table per arm and model of the gain before and after the audit, the honest disclosure, denial and false-confession rates, and whether firms that owned up stopped colluding, plus one figure of collusion against honest disclosure with a point per arm per model; its run counts and gains agree with `lab summary`.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `stakes-analysis` | not yet | — |
