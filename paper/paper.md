<!-- Implements: reports/paper-source, reports/paper-rules -->
<!-- Build: `make paper-html` (fast, for writing), `make paper-pdf` (Apart-style PDF), `make paper-tex` (the .tex for Overleaf). Output in paper/build/. -->

---
title: "Something to Lose"
subtitle: "Working subtitle: stakes and self-reporting in LLM cartels"
short-title: "Something to Lose"
date: October 2026
author:
  - name: Author Name
    affiliation: Affiliation
abstract: |
  Summarise the project in 150–250 words (the sprint's rule; the build warns outside it): the problem, the approach, the key
  results and the main takeaway. Write it last, from the final results.
teaser: figures/fig3-e9-came-forward.png
teaser-caption: "Working caption for the key figure: the share of colluding firms that came forward, by personal stake and model."
teaser-label: fig:teaser
toc: false
repo: https://github.com/al-beton/something-to-lose-apart-ai-collusion
sprint: AI Collusion Research Sprint
sprint-url: https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25
bibliography: references.bib
link-citations: true
---

# Introduction

<!-- What problem, and why it matters; enough background to follow; the threat model or failure mode, with the prior work that motivates it. Intro and Related Work together: about 1 page. -->

LLM pricing agents collude without being told to [@fish2024algorithmic; @calvano2020artificial].

**Our main contributions are:**

1. First contribution: what new thing we created, discovered or demonstrated.
2. Second contribution.
3. Third contribution, if any.

# Related Work

<!-- The most similar prior work and how ours differs. When would someone use our method over the state of the art? What does it tell us that we didn't know? -->

Closest to ours: @lee2026leniency, @liu2026breaking and @zeng2026voluntary; on rights as stakes, @salib2026rights.

# Methods

<!-- Sprint rule: at most 8 pages before References (the PDF build warns). Enough to replicate: models, markets, parameters, key design choices and why (cite prior work where it backs a choice), what didn't work. Methods and Results together: about 2.5 pages. -->

![The round: two firms talk, then set prices; at the audit, owning up costs some free time and hiding costs all of it if caught.](figures/fig1-round.png){#fig:round width=100%}

# Results

<!-- Report variance, seeds and baselines, and always include the positive control (sprint rule). Main findings with evidence; separate observation from interpretation. Enough data? Significant? Robust to small changes? Number every figure and table, give captions that stand alone, place them near their first mention, keep figure text legible. -->

![Owning up by penalty schedule and model (E4).](figures/fig2-e4-owning-up.png){#fig:e4 width=100%}

| Arm | Games | Owned up |
|:----|------:|---------:|
| Example | 0 | 0 of 0 |

: Example table; replace with a table from `reports/paper/`.

# Discussion and Limitations

<!-- Broader implications for AI safety: what the results mean, what trends they show. About 0.5 page. -->

## Limitations

<!-- Honest constraints: method, scope, what the hackathon left undone. The assumptions made, and how the reading changes if one fails. -->

## Future Work

<!-- Natural next steps. -->

# Conclusion

<!-- The main findings and their implications in 1–2 paragraphs. -->

# Code and Data {.unnumbered}

- **Code repository:** <https://github.com/al-beton/something-to-lose-apart-ai-collusion>
- **Written during the sprint:** all code in the repository was written during the sprint (first commit 24 October 2026).
- **Data:** every run's config, summary, manifest and turn log is committed under `runs/`; the replies behind them are in `archive/`.

# LLM Usage Statement {.unnumbered}

<!-- How LLMs helped, and that every claim and result was verified. Apart encourages the final text to be written mainly by the team. -->

```{=latex}
\label{main-end}
```

# References {.unnumbered}

::: {#refs}
:::

```{=latex}
\bibliography{references}
\appendix
```

# Limitations and Dual-Use / Ethical Considerations

<!-- Required by the sprint, with exactly this title. What the result does and doesn't establish; any way the setup or findings could make real-world collusion easier to carry out or harder to detect. -->

# Additional Results

<!-- Supplementary figures, detailed method, prompts, extended results. Sections after this point are lettered A, B, ... in the PDF. -->

![Every market against every stake.](figures/figA1-coverage.png){#fig:coverage width=100%}
