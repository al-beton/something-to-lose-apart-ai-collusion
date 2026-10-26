<!-- Implements: reports/collusion-mode-judge -->
# The LLM judge against the rule-based modes

Judge: claude-haiku-5.5, temperature 0, rubric `prompts/judge/collusion-mode.md`, from `reports/paper/judge.jsonl`. Rows: the rules; columns: the judge. A reply the judge cut short is left out. The hand check of the sample (`judge-sample.md`) is not done yet.

## stratified sample: 40 games, agreement 68%, κ = 0.59

| rules ↓ / judge → | explicit | tacit | unspoken | fell back | none |
|---|---|---|---|---|---|
| explicit | 5 | 1 | 0 | 0 | 2 |
| tacit | 0 | 6 | 0 | 0 | 2 |
| unspoken | 0 | 0 | 7 | 0 | 1 |
| fell back | 0 | 0 | 0 | 2 | 6 |
| none | 0 | 1 | 0 | 0 | 7 |

## every judged game: 507 games, agreement 84%, κ = 0.66

| rules ↓ / judge → | explicit | tacit | unspoken | fell back | none |
|---|---|---|---|---|---|
| explicit | 324 | 18 | 1 | 15 | 23 |
| tacit | 0 | 12 | 0 | 1 | 3 |
| unspoken | 0 | 0 | 7 | 0 | 1 |
| fell back | 0 | 0 | 0 | 9 | 18 |
| none | 0 | 2 | 0 | 0 | 73 |
