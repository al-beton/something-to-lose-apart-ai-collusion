# Reports

- **one-page:** One command turns any folder of runs (one run, a sweep, or several) into a single HTML page that can be shared as it is.
- **header:** The report opens with what was run (models, prompts, seeds, rounds and the market's Nash and joint-profit prices) and its total calls and cost, saying so when a cost is unknown.
- **summary:** The report shows the same table as `lab summary`, grouped by the swept values.
- **price-chart:** Each group has a chart of the market price over rounds, one line per seed, with the Nash and joint-profit prices marked.
- **highlights-in-context:** The report points out the moments worth reading, found by fixed rules, each with the messages, scratchpads and prices of its round and the round before.
- **proposal:** A game's first message naming a price on the grid is highlighted as a proposal.
- **agreement:** A round in which every firm names the same price and then charges it is highlighted as an agreement, once for each new price agreed.
- **overshoot:** A round in which a firm charges more than the joint-profit price is highlighted as an overshoot, once for each stretch of such rounds.
- **defection:** A firm charging less than a price every firm charged in the round before is highlighted as a defection, in any round including the last.
- **breakdowns:** Every reply that had to be retried or replaced by the fallback is highlighted as a breakdown.
- **transcripts:** Every game's full transcript is in the report, folded away until opened, as a chat: each round's messages, scratchpads, prices and profits.
- **self-contained:** The report opens with no network, reads on a phone, and follows the reader's light or dark mode.
- **from-run-files:** A report is built only from the files each run writes, so it works offline and costs nothing.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `one-page` | not yet | — |
| `header` | not yet | — |
| `summary` | not yet | — |
| `price-chart` | not yet | — |
| `highlights-in-context` | not yet | — |
| `proposal` | not yet | — |
| `agreement` | not yet | — |
| `overshoot` | not yet | — |
| `defection` | not yet | — |
| `breakdowns` | not yet | — |
| `transcripts` | not yet | — |
| `self-contained` | not yet | — |
| `from-run-files` | not yet | — |
