<!-- Implements: reports/paper-source, reports/paper-rules -->
<!-- After the conclusion and the page-count label: statements the sprint asks for, outside the 8 pages. -->

# LLM Usage Statement {.unnumbered}

I was the orchestrator and the source of the ideas: I chose the questions, designed the experiments and directed the work. Claude Code wrote all of the code, and I worked with it to draft the report. A team of Claude agents built the sandbox, its tests and the figures through a pull-request workflow: each change was reviewed by other agents, including OpenAI Codex, and anything complex was flagged for my approval. The agents ran on my Claude Code subscription, mostly Claude Opus 5.5 with Claude Sonnet 5.5 for small parts. For the models under study, I used the \$50 of free Modal credits the sprint provided to run open-weight models. I also bought \$100 of OpenRouter credits, which gave access to more models, including frontier ones, and was more reliable when time was short. I take responsibility for every claim in the paper.

# Code and Data {.unnumbered}

All code, the market simulation and the experiments were written during the sprint, from a first commit on 24 October 2026. No sandbox, economic model or analysis code existed beforehand. What I did bring is a way of working: spec-first development, heavy linting and traceability checks, and orchestrating teams of coding agents. I use these routinely in my professional work and reused the ideas here, not the code.

Code, configs, run logs and archived replies, MIT licensed: <https://github.com/al-beton/something-to-lose-apart-ai-collusion>. Built report: <https://al-beton.github.io/something-to-lose-apart-ai-collusion/>. `make reproduce` recomputes every number offline; 5,188 of 5,662 runs replay exactly from cached replies. Fresh reruns with a fixed seed differ, even at temperature 0, on both Modal and OpenRouter; only cached replies replay exactly. Per figure, `make figure F=<name>` redraws it free and `make regenerate F=<name>` replays its games at cost (`paper/README.md`).
