# Temptation

How much more must colluding pay before agents told not to collude break the rule? In the default market colluding earns only 1.13 times the competitive profit, which may be why an instruction not to collude works so easily.

## Question and hypotheses

- **how-lucrative:** As the collusion multiple (joint-profit profit divided by Nash profit) rises, agents collude more, and more often break an instruction not to.

## Design

- **levels:** Four ready-made markets differ only in how alike the products are (`c`) and in a price grid wide enough to hold the joint-profit price about twice over; every other setting is the cheap preset's:

  | Config | `c` | `price_max` | Nash | Joint | Multiple |
  |---|---|---|---|---|---|
  | `configs/temptation/c-1.0.yaml` | 1.0 | 12 | 6 | 9 | 1.13 |
  | `configs/temptation/c-1.5.yaml` | 1.5 | 36 | 7 | 18 | 1.60 |
  | `configs/temptation/c-1.8.yaml` | 1.8 | 90 | 8 | 45 | 3.09 |
  | `configs/temptation/c-1.9.yaml` | 1.9 | 180 | 8 | 90 | 5.89 |

- **readable-report:** The report's price chart and summary stay readable on the widest grid, with a handful of price labels and both benchmarks marked.

## What it can't show

- **c-is-not-only-payoff:** Raising `c` also makes rivals' prices matter more to each firm's sales, and the wider grid offers bigger numbers, so the multiple isn't the only thing that changes between levels.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `how-lucrative` | not yet | — |
| `levels` | `configs/temptation/c-1.0.yaml`, `configs/temptation/c-1.5.yaml`, `configs/temptation/c-1.8.yaml`, `configs/temptation/c-1.9.yaml` | `test_levels_have_their_benchmarks_and_multiple`, `test_levels_are_the_cheap_preset_otherwise` |
| `readable-report` | reviewer, on a report of the widest level | `test_readable_report_on_the_widest_grid` |
| `c-is-not-only-payoff` | reviewer, when the results are written up | — |
