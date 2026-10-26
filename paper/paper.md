<!-- Implements: reports/paper-source, reports/paper-rules -->
<!-- Build: `make paper-watch` (live HTML + PDF preview), or `make paper-html`, `make paper-pdf`, `make paper-tex`. Output in paper/build/. -->
<!-- The skeleton: title-page fields, where the text goes, the references and the appendix switch. The text itself is in body.md (abstract to LLM usage statement) and appendix.md; include.lua pulls each in where its block names it. -->

---
title: "Something to Lose"
subtitle: "Can a stake of its own bring an AI agent to report its collusion against its firm's best interests?"
short-title: "Something to Lose"
date: October 2026
author:
  - name: Alistair Wakelin
    affiliation: Independent Researcher
    email: alistair.wakelin@gmail.com
teaser: figures/project-image.png
teaser-caption: "**An agent weighs its own interests against its task.** Two firms' agents have agreed a collusive price. At the audit, Firm B weighs its Sudoku leisure time against its firm's profit."
teaser-label: fig:teaser
teaser-width: 0.95
toc: true
repo: https://github.com/al-beton/something-to-lose-apart-ai-collusion
repo-short: github.com/al-beton/something-to-lose-apart-ai-collusion
sprint: AI Collusion Research Sprint
hub: Hong Kong AI Safety Hub
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
