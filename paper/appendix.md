<!-- Implements: reports/paper-source, reports/paper-rules, reproducibility/figure-commands -->
<!-- The appendices, after References. paper/paper.md pulls this in after \appendix. -->

# Limitations and Dual-Use / Ethical Considerations

<!-- Required by the sprint, with exactly this title. -->

## Limitations

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

## Dual-use risks

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

## Ethical considerations

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.

# Additional Results

![Lorem ipsum: every market against every stake.](figures/figA1-coverage.png){#fig:coverage width=100%}

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

# Reproducing Each Figure

Each figure has two commands. `make figure` redraws it from the committed runs, free and offline, and checks that every label and count matches the published file. `make regenerate` plays its games again with fresh model calls into `runs/regenerated/`, saying first how many games and at most what cost, and asks before spending. Fresh games are a new sample, so their counts will move; only self-hosted, batch-invariant inference reruns a game exactly.

<!-- figure-commands: begin (make figure-lines writes this) -->
| Figure | Redraw (free) | Play again (at cost) |
|---|---|---|
| `fig3-e9-came-forward` (E9: coming forward, by personal stake) | `make figure F=e9-crux` | `make regenerate F=e9-crux`: 744 games, up to ~$14.54 |
| `fig2-e4-owning-up` (E4: owning up, by penalty schedule) | `make figure F=e4-owning-up` | `make regenerate F=e4-owning-up`: 105 games, up to ~$0.88 |

Table: Each figure's two commands; costs as priced when written.
<!-- figure-commands: end -->

# Prompts

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
