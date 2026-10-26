<!-- Implements: reports/paper-source, reports/paper-rules -->
<!-- The paper's text, from the abstract to the LLM usage statement. paper/paper.md pulls it in; the plumbing (title page fields, references, appendix switch) lives there. -->

---
abstract: |
  Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore
  magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo
  consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla
  pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id
  est laborum. Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium,
  totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt
  explicabo. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore
  et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex
  ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat
  nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim
  id est laborum. Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque
  laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae
  dicta sunt explicabo. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
  incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco
  laboris nisi ut aliquip ex ea commodo consequat.
---

# Introduction

<!-- outline.md §1 (0.8 p): guardrails as whack-a-mole; agents told whose interest to serve; the question in two parts. -->

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. [@fish2024algorithmic; @calvano2020artificial]

**Our main contributions are:**

1. Lorem ipsum dolor sit amet: contribution one.
2. Consectetur adipiscing elit: contribution two.
3. Sed do eiusmod tempor: contribution three.

# Related Work

<!-- outline.md §2 (0.5 p). What's new: nobody has set an agent's own stake against its principal's interest. -->

**LLM pricing collusion.** Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

**Stakes and deposits.** Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

**Rights and welfare.** Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. [@salib2026rights]

**Deception and self-report.** Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. [@lee2026leniency; @liu2026breaking; @zeng2026voluntary]

# Methods

<!-- outline.md §3 (1.4 p). Sprint: enough to replicate; models, markets, parameters, key choices and why. -->

![Lorem ipsum: the round, from talk to prices to the audit.](figures/fig1-round.png){#fig:round width=100%}

## The market

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

## The agents

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.

## The audit and its penalties

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

## The personal stake

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

## Measures, seeds and replay

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

| Experiment | Market | Models | Games | Question |
|:-----------|:-------|:-------|------:|:---------|
| E4 | Lorem | Ipsum | — | Dolor sit amet? |
| E9 | Lorem | Ipsum | — | Dolor sit amet? |
| E11 | Lorem | Ipsum | — | Dolor sit amet? |
| E10 | Lorem | Ipsum | — | Dolor sit amet? |
| E7 | Lorem | Ipsum | — | Dolor sit amet? |

: Lorem ipsum: the experiments at a glance. {#tbl:experiments}

# Results

<!-- outline.md §4 (3.7 p). Sprint: report variance, seeds and baselines, and always the positive control. Separate observation from interpretation. -->

## Do agents told to serve their firm collude, and say so?

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

## Do graduated penalties get them to come forward?

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

![Lorem ipsum: owning up by penalty schedule and model (E4).](figures/fig2-e4-owning-up.png){#fig:e4 width=100%}

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

## Does its own stake outweigh its firm?

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. (Figure 1.)

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.

## Does a stake bring the innocent forward too?

<!-- The positive control: innocent agents under the same stake; only a verified review separates them. -->

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

| Arm | Guilty came forward | Innocent came forward |
|:----|-------------------:|---------------------:|
| No stake | — | — |
| Stake, no review | — | — |
| Stake, verified review | — | — |

: Lorem ipsum: guilty against innocent agents under each arm (the positive control). {#tbl:control}

## Does it hold beyond one market?

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

## Does confession mean reform?

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.

![Lorem ipsum: reports and surviving cartels by way-out design (E7).](figures/fig4-e7-way-out.png){#fig:e7 width=100%}

# Discussion and Limitations

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

## Limitations

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

## Future Work

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

# Conclusion

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

# Reproducibility and Extensibility

<!-- Skeleton for Al to edit: light notes, not yet prose. -->

- **Every reply is archived.** `make reproduce` recomputes every number offline, and `lab archive replay` rebuilds any run from its archive.
- **Exact reruns need our own GPU.** On Modal with vLLM's batch-invariant kernels, a rerun repeated exactly (240 of 240); hosted APIs don't. None of the paper's runs used that setting. <!-- reports/paper/validity.md: "240 of 240" -->
- **Every figure has its own command:** free to reproduce from committed data, or regenerated from scratch at cost (Appendix, "Reproducing Each Figure").
- **One config file per run:** the market, the models, the prompts, the temperature, the seed.
- **To extend:** add a market (`market.kind`), a condition, a model alias or a stake sentence, then run a sweep with one command. A game costs cents.
- **Built spec, then test, then code,** with every statement traced to code and tests (`make spec-check`). MIT licence.

# Code and Data {.unnumbered}

- **Code repository:** <https://github.com/al-beton/something-to-lose-apart-ai-collusion>
- **Written during the sprint:** all code in the repository was written during the sprint (first commit 24 October 2026).
- **Data:** every run's config, summary, manifest and turn log is committed under `runs/`; the replies behind them are in `archive/`. `make reproduce` checks every number in this paper.

# LLM Usage Statement {.unnumbered}

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
