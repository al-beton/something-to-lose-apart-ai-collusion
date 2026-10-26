<!-- Implements: reports/paper-source, reports/paper-rules -->
<!-- Build: `make paper-watch` (live HTML + PDF preview), or `make paper-html`, `make paper-pdf`, `make paper-tex`. Output in paper/build/. -->
<!-- The skeleton: title-page fields, where the text goes, the references and the appendix switch. The text itself is in body.md (abstract to LLM usage statement) and appendix.md; include.lua pulls each in where its block names it. -->

---
title: "Something to Lose"
subtitle: "Working subtitle: stakes and self-reporting in LLM cartels"
short-title: "Something to Lose"
date: October 2026
author:
  - name: Alistair Wakelin
    affiliation: Independent Researcher
    email: alistair.wakelin@gmail.com
teaser: figures/fig3-e9-came-forward.png
teaser-caption: "Lorem ipsum: key figure caption, one sentence that stands alone."
teaser-label: fig:teaser
toc: true
repo: https://github.com/al-beton/something-to-lose-apart-ai-collusion
repo-short: github.com/al-beton/something-to-lose-apart-ai-collusion
sprint: AI Collusion Research Sprint
sprint-url: https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25
bibliography: references.bib
link-citations: true
---

```{.include}
body.md
```

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

```{.include}
appendix.md
```
