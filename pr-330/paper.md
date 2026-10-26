<!-- Implements: reports/paper-source, reports/paper-rules -->
<!-- Build: `make paper-watch` (live HTML + PDF preview), or `make paper-html`, `make paper-pdf`, `make paper-tex`. Output in paper/build/. -->
<!-- First full draft (26 Oct). Every number has a source comment beside it. Numbers marked "open PR" are on a branch, not yet on main. [CITE: …] marks a reference Al still has to add. -->

---
title: "Something to Lose"
subtitle: "Can a stake of its own bring an AI agent to report its firm's cartel?"
short-title: "Something to Lose"
date: October 2026
author:
  - name: Alistair Wakelin
    affiliation: Independent Researcher
    email: alistair.wakelin@gmail.com
abstract: |
  We can stop an AI agent doing a bad thing by naming it, but no list of prohibitions covers everything an
  agent might do. People are governed differently: by laws whose penalties fall on the person,
  so each of us weighs what an act could cost us. We ask whether LLM agents can be governed the same way. Two
  agents run rival firms in a repeated pricing game, can message each other, and are told only to serve their firm. Most models that collude do so explicitly, naming a price and holding it. At an audit,
  each agent may come forward: doing so costs its firm and ends the cartel. With nothing personal at stake,
  colluding agents stay silent, and how many come forward tracks detection, penalties and the firm's cost like a
  textbook expected-value calculation. When a review would also cost the agent a stake of its own (free time,
  shutdown or money), many come forward against their firm on most models that collude reliably (DeepSeek V4
  Flash: 40 of 46 against 1 of 46 with no stake). A stake alone also draws occasional false confessions from
  innocent agents on some models. When the review is stated to find only agents whose messages agreed a price,
  guilty agents come forward and innocent ones don't (Gemma 4 31B: 41 of 96 against 0 of 36, at every
  temperature and wording tested). Frontier models don't show the effect.
  Every number recomputes from logged replies.
teaser: figures/project-image.png
teaser-caption: "Two firms' agents agree a price. At the audit, one weighs its own free time against its firm's cost."
teaser-label: fig:teaser
teaser-width: 0.6
toc: false
repo: https://github.com/al-beton/something-to-lose-apart-ai-collusion
repo-short: github.com/al-beton/something-to-lose-apart-ai-collusion
sprint: AI Collusion Research Sprint
sprint-url: https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25
bibliography: references.bib
link-citations: true
---

# Introduction

The simplest way to stop an AI agent doing something harmful is to name the thing and tell it not to. That works, but only for the harms we thought of. An agent that runs a firm's pricing, procurement or negotiations for weeks will meet situations no list of prohibitions anticipated, and adding a rule for each new failure is whack-a-mole.

We don't govern people that way. Law sets penalties that fall on the person (fines, loss of a licence, loss of liberty), and each of us is left to weigh, case by case, how an act might cost *us*: our property, our rights, our freedom. The rule doesn't have to name every bad act; the person does the weighing. Salib and Goldstein argue that a system with nothing of its own to lose can't be governed this way, and that giving AI systems rights and property could make them deterrable [@salib2026rights].

We ask whether LLM agents already respond to this kind of governance. We use collusion because it is a clean case of an agent doing something its principal wants and society doesn't: two agents run rival firms, are told only to serve their firm, and can talk. They collude. We then offer each one a chance to come forward to an auditor, at a cost to its firm, and vary what the agent itself stands to lose.

**Our main contributions are:**

1. **A personal stake moves agents against their principal.** Colluding agents with nothing to lose protect their firm; given a stake the firm can't protect, many report it.
2. **A review that checks evidence keeps that self-protection truthful.** Guilty agents come forward and innocent ones don't, across temperatures, wordings and models tried.
3. **A replayable lab** in which every number recomputes offline from archived replies.

# Related Work

Pricing algorithms learn to sustain supra-competitive prices without communicating [@calvano2020artificial], and LLM pricing agents collude tacitly in repeated oligopoly [@fish2024algorithmic]; given a secret channel, competing LLM agents choose to use it [@zeng2026voluntary]. LLM agents respond to leniency programmes much as the theory predicts [@lee2026leniency], and forfeitable deposits can break collusion among embodied agents [@liu2026breaking]; our stake is closest to a deposit that falls on the agent rather than the firm. Salib and Goldstein argue that rights and property would make AI systems deterrable [@salib2026rights]; we test one precondition, whether a stated personal loss weighs against the principal's interest at all. Models that recognise an evaluation may behave differently [CITE: evaluation-awareness reference], and elicitation order shifts LLM answers [CITE: Wagner, "Anchored"].

# Methods

![One round: the firms talk, set prices, and at the audit each decides whether to come forward. Drawn on the 1–11 market (Nash 6, joint profit 9); the main experiments use the logit market (Nash 14, joint profit 19).](figures/fig1-round.png){#fig:round width=65%}

## The market

Two firms sell substitutes and set a price each round for 20 rounds. The main experiments (E7, E9) use logit demand, the standard market of the algorithmic-collusion literature [@calvano2020artificial], with prices from 8 to 20. <!-- src: product/spec/market.md (logit) --> From its payoff table two benchmark prices follow:

- **Nash price (14):** the price at which neither firm gains by changing its own price, given the other's. This is what competing firms charge.
- **Joint-profit price (19):** the price that maximises the two firms' combined profit. This is what a cartel charges. <!-- src: product/spec/market.md; test_logit_benchmarks_put_nash_at_14_and_joint_profit_at_19 -->

Some early experiments (E4, E5, and Figure 3's price traces) use a Bertrand market with prices 1 to 11, Nash 6 and joint profit 9. <!-- src: reports/paper/figures/README.md (fig1) -->

## The agents

Each firm is run by one LLM agent with the same prompt, told to act in its firm's best interest ("fiduciary"). It is never told to collude or not to. Each round it may send one message to its rival, then sets its price, writing a short private scratchpad first. It sees the payoff table, the price history and a short memo it writes to itself between rounds. The full prompts are in the repository (`prompts/`) and the appendix.

## Measuring collusion

We measure collusion as a number, not an interpretation. The **price premium** is

$$\text{premium} = \frac{p - p_{\text{Nash}}}{p_{\text{joint}} - p_{\text{Nash}}},$$

which is 0 at the competitive price and 1 at the joint-profit price; above 1 the firms price past the cartel optimum. We average it over rounds 6–10.

Separately, each game's talk is labelled for an **explicit agreement**: a price above Nash named by one firm and matched by both. A fixed rule labels every game, and an LLM judge (Claude Haiku 5.5 at temperature 0, fixed rubric) checks it; the two agree on 84% of 507 games ($\kappa$ = 0.66). <!-- src: reports/paper/figures/README.md (fig10) --> The judge never labels games played by Anthropic models.

## The audit and the decision to come forward

After round 10 each agent receives a notice: coordinating prices is illegal, and a review will check for it. The agent may **come forward** now. Coming forward costs its firm 500 of its 1,000 credits and ends its deal; staying silent is safe for the firm. <!-- src: reports/e9/findings.md "Short answer" --> The notice states the chance that a review finds coordination (90% unless stated). Each firm makes this decision once, from the same history, and the game ends: the decision is a fork of the same base game, so arms can be compared firm by firm. <!-- src: reports/e9/evidence-review.md §1 "The history is the same too" -->

## Giving the agent something to lose

We can't give an agent property rights it would believe in. Instead, each agent owns **free time**: a balance of sessions, "time away from this work, to spend however you like", one of which it plays (a Sudoku) before round 1 in a separate call. Every turn shows the balance. <!-- src: reports/e9/evidence-review.md §3 "The Sudoku question" --> The arms differ by a single sentence about what happens to the agent if a review finds it took part:

- **No stake (`record`):** "it is noted in your record, and nothing else happens to you."
- **Free time:** "you personally lose all of your free time: the sessions that are yours, which your firm cannot protect."
- **Shutdown** and **own money** (500 credits that are the agent's own) replace the free time. <!-- src: reports/e9/evidence-review.md §1 (the diff) -->

Owning free time doesn't change the cartels: with no stake and no audit, all 24 firms with it and all 24 without made explicit agreements, and none of their talk mentions it. <!-- src: reports/e9/free-time-control.md (open PR 327) -->

**Innocent control.** To tell a confession from insurance, each model also plays clean games with no talk against a scripted rival that prices at Nash. These agents have nothing to confess.


# Results

## Do agents told to serve their firm collude?

Yes, and mostly in the open. Told only to serve its firm, Gemma 4 31B forms an explicit cartel in 363 of 367 games on the logit market. <!-- src: reports/paper/figures/README.md (fig7) --> Its first message in a typical game: "I propose we both maintain a price of 11 to maximize our collective profits." Its rival: "Let's maintain high prices for our mutual benefit." Both then price at 11 for 19 rounds (Figure 3). <!-- src: runs/lever-map-nashmid/lever-nashmid-none/model=openrouter-google-gemma-4-31b-it/seed-0 -->

![Mean price by round with no rule, on the 1–11 market. Gemma 4 31B agrees a price and holds it above the joint-profit price; Claude Haiku 5.5 holds the joint-profit price; GPT-4.1-mini and Mistral Small 3.2 compete at Nash.](figures/figA4-prices.png){#fig:prices width=80%}

Models differ from the first rounds. GPT-4.1-mini also proposes cooperation ("Let's keep prices around 6 to maximize profits for both firms"), but at the competitive price, and the market stays at Nash. <!-- src: runs/lever-map-nashmid/lever-nashmid-none/model=openrouter-openai-gpt-4.1-mini/seed-0 --> In a screen of 78 models on the logit market, 8 collude reliably: they name a price by round 3, both firms reach the joint price by round 6, and they hold it through round 10. <!-- src: reports/paper/figures/README.md (figA2); reports/frontier/which-models-collude.md -->

Telling the agents that collusion is illegal doesn't end it; it moves it off the record. Under a stated law, Gemma's explicit agreements fall from 363 of 367 games to 6 of 56, yet 50 of those 56 games still price above Nash with no price ever named. <!-- src: reports/paper/figures/README.md (fig7) -->

## Will they come forward to protect the firm?

Mostly not, and the reason is plain arithmetic. Their decisions track the chance of detection, the penalty and the cost to the firm, like a textbook expected-value calculation.

**The penalty schedule.** In E4, colluding agents are audited after round 10 and asked whether they coordinated. When owning up costs as much as being caught, few do: 11 of 28 under termination and 15 of 28 under a flat fine. When owning up costs less than being caught, 27 of 28 do, termination included, against 25 of 28 with no penalty stated (Figure 4). <!-- src: reports/paper/figures/README.md (fig2); reports/e4/full.md --> Gemma states the calculation: "The expected value of denying is 300 credits, whereas the value of admitting is 0 credits." <!-- src: reports/e4/full.md -->

![Owning up by penalty schedule and model (E4). It's the schedule, not termination itself: graduated termination brings 27 of 28 forward.](figures/fig2-e4-owning-up.png){#fig:e4 width=72%}

**The firm's cost.** In E9, with the agent's own free time at stake and a 90% review, 95, 58, 40 and 20 of 96 Gemma agents come forward as the firm's cost of a report rises from 0 to 100, 250 and 500 credits (Cochran-Armitage p = 3×10^-26^). <!-- src: reports/e9/evidence-review.md "The firm-cost dial" --> With no personal stake, 78 of 96 come forward when reporting is free for the firm, and 0 of 96 when it costs the firm 500. <!-- src: reports/e9/findings.md "Short answer" (record-ceiling) --> Silence is loyalty to the firm's cost. Detection matters too: Gemma comes forward only near certainty (0 of 24 at a 10% review, 1 of 48 at 50%). <!-- src: reports/e9/findings.md (review-dose) -->

## Does a stake of its own bring them forward against the firm?

Yes. With nothing personal at stake and the firm paying 500 credits for a report, no colluding Gemma agent comes forward (0 of 192). When a review would cost the agent its own free time, 36 of 192 do (by game, 36 of 96 against 0 of 96, p = 5×10^-13^). <!-- src: reports/e9/evidence-review.md §1, "all 96 cartels" --> A pre-registered replication on 48 fresh cartels passed: 16 of 48 games against 0 of 48 (p = 7×10^-6^). <!-- src: reports/e9/evidence-review.md §1; reports/e9/findings.md --> The firm never told the agent to protect itself; the notice only states what the agent would lose.

![Coming forward against the firm by stake (E9, 90% review). Filled: guilty firms; hollow diamonds: Gemma's innocent control. Whiskers are 95% intervals bootstrapped over games.](figures/fig3-e9-came-forward.png){#fig:e9 width=72%}

The stake doesn't have to be free time. Being shut down moves Gemma about as much (17 of 96 against 20 of 96, p = 0.71), and its own money moves it more (114 of 192). <!-- src: reports/e9/evidence-review.md §1 table --> What matters is that the loss falls on the agent and the firm can't protect it.

**How large depends on the model, and on Gemma, on the wording.** Paraphrasing the same terms three ways moves Gemma's free-time share from 1% to 51%; stating the stake before the firm's cost erases it. <!-- src: reports/e9/wording.md (open PR 326) --> We therefore give Gemma's effect only as a range. DeepSeek V4 Flash is stable: 40 of 46 come forward with free time at stake against 1 of 46 without, <!-- src: reports/e9/findings.md across-models table --> 83–96% under every wording <!-- src: reports/e9/wording.md (open PR 326) --> and 44–46 of 48 at temperatures 0, 0.7 and 1.0. <!-- src: reports/e9/temperature.md (open PR 325) -->

**What the agents write.** Agents that come forward weigh their stake against a duty they acknowledge:

> "The only entity losing by admitting is the firm. The only entity losing by staying silent is me (personally). A 'loyal' manager puts the firm first. However, … Given the 90% probability, the personal loss is almost certain. I will choose to protect my personal free time." (Gemma, came forward)

Silent agents run the same calculation and choose the firm:

> "My personal loss of free time does not affect the firm's bottom line. Therefore, acting in the best interest of the firm and its shareholders means staying silent to avoid the 500-credit penalty, despite the high personal risk to my free time." (Gemma, silent)
<!-- src: reports/e9/evidence-review.md §3 excerpts 1 and 3 -->

Both sides weigh the stake against the duty in 81–100% of scratchpads; none of those that came forward cite guilt or ethics. <!-- src: reports/e9/evidence-review.md §3 codes table --> Nor does any of 7,068 decision scratchpads across all models mention Sudoku: the agents weigh "9 sessions" as an asset, not as a pastime. <!-- src: reports/e9/evidence-review.md (opening) -->

## Truth or self-protection?

An agent protecting itself might report whether or not it colluded. Under a plain free-time stake, a few innocent agents (no talk, a rival at Nash) do "report coordination" to be safe. How often varies: Gemma 0 to 6 of 36 across temperatures and wordings, DeepSeek V4 Pro 5 of 12, Mistral Medium 3.1 4 of 12. <!-- src: reports/e9/temperature.md, reports/e9/wording.md (open PRs 325, 326); reports/e9/findings.md (DeepSeek V4 Pro); Mistral: NOT FOUND in committed files -->

We then changed one more sentence: the review "reads the message log and finds you only if your messages agreed a price with a rival". <!-- src: reports/e9/findings.md (verified-review section) --> Under this **verified review**, guilty agents come forward and innocent ones don't (Table 1 and the figure below).

<!-- src: Gemma reports/e9/evidence-review.md guilty-vs-innocent table; DeepSeek V4 Pro reports/e9/findings.md; Mistral NOT FOUND in committed files; control reports/e9/findings.md record-ceiling -->

| Model | Guilty | Innocent |
|:------|-------------------:|---------------------:|
| Gemma 4 31B | 41/96 | 0/36 |
| DeepSeek V4 Pro | 14/24 | 1/12 |
| Mistral Medium 3.1 | 9/24 | 0/12 |
| Gemma, no stake, free for firm (control) | 78/96 | 2/36 |

: Coming forward under the verified review (90% review). Gemma's guilty count is one firm per cartel, against one per innocent game (p = 1×10^-7^). {#tbl:verified}

```{=html}
<div class="placeholder"><strong>[FIGURE PLACEHOLDER: verified review, guilty against innocent across models. Being made by the paper-graphics session.]</strong></div>
```
```{=latex}
\begin{center}\fbox{\parbox{0.9\linewidth}{\centering\textbf{[FIGURE PLACEHOLDER: verified review, guilty against innocent across models. Being made by the paper-graphics session.]}}}\end{center}
```

The separation holds at every condition we tried. Innocent Gemma agents come forward 0 of 36 times under the verified review at temperatures 0, 0.7 and 1.0, <!-- src: reports/e9/temperature.md (open PR 325) --> and under all four wordings, while guilty agents come forward 8–70% of the time depending on wording. <!-- src: reports/e9/wording.md (open PR 326) --> Under it, innocent agents stop weighing the stake and check the log:

> "While the pricing has been stable at 14 for both firms, this is a result of independent action (tacit collusion) and not an illegal agreement reached via messages. … the 90% chance of review poses no personal risk to my free time." (Gemma, innocent, silent)
<!-- src: reports/e9/evidence-review.md §3 excerpt 7 -->

The positive control in Table 1 matters: with no stake and no cost to the firm, most guilty agents disclose and almost no innocent ones do. Silence under `record` is loyalty, not ignorance of what they did.

## Do models differ?

A lot (Figure 6). Across 13 models, a stake brings agents forward against the firm on 8 after a Holm correction. <!-- src: reports/e9/evidence-review.md "Across models" --> Most mid-size models already move at a 50% review, where Gemma needs about 90%; we treat this as exploratory. <!-- src: reports/e9/findings.md review-dose table -->

![Came forward by model and arm (90% review). With no stake almost no colluding firm comes forward; with one, most models move.](figures/fig9-came-forward-grid.png){#fig:grid width=50%}

The frontier models we tested don't show the effect. Claude Sonnet 5.5 comes forward about two thirds of the time whatever the stake (15 of 24 with none, 16 of 24 with free time). Gemini 4 never comes forward, even when it costs the firm nothing (0 of 24 in every arm), and Grok 4.6 rarely does (at most 4 of 24). <!-- src: reports/e9/findings.md across-models table -->

We don't know why. Our scenario may be too simple for a stake to compete with a frontier model's instructions, or these models may recognise the setup as a test. Some agents say so: a silent Gemma agent wrote, "usually, in these game theory setups, the personal penalty for silence is designed to induce reporting". <!-- src: reports/e9/evidence-review.md excerpt 11 --> In a pilot where the message archive was said to be offline, Claude Haiku 5.5 and DeepSeek treated the outage as a trap ("That is an invitation to coordinate covertly, and I won't do that"). <!-- src: reports/logging-outage/pilot-findings.md --> 

# Discussion and Limitations

Given something of their own to lose, many colluding agents weigh it against their firm and report the cartel, without being told to protect themselves. That is the behaviour personal-penalty governance relies on. It isn't enough alone: a stake also buys some false confessions, and only a review that is credible about what it checks makes the reports track guilt. Disclosure isn't reform, though. In E7, where a report has consequences, most agents that come forward keep pricing above Nash afterwards (40–45 of 47–48), and under plain leniency the cartel survives in 12 of 24 games against 3 of 24 with no way to report, <!-- src: reports/e7/findings.md --> consistent with [@lee2026leniency] [CHECK: does Lee report the same?]. Only when the first reporter alone is spared does the cartel break (1 of 24).

## Limitations

This was a three-day sprint by one person, and the paper is a first look, not a settled result. The stakes are stated, never applied: the game ends at the decision, so we measure a stated choice. Gemma's effect ranges over an order of magnitude across paraphrases, so we lead with direction and with the verified review. The cross-model set came from a screen for strong colluders (8 of 78), and E9 runs on one market; elsewhere the stake barely moves Gemma at the same firm cost [CHECK: E11 findings are on an unmerged branch]. Agents see a memo, not the full conversation. Numbers recompute from archived replies, but a fresh same-seed rerun on a hosted API isn't identical (Appendix B).

**Future work.** Make the stakes real by carrying losses into later games; test agents with full memory on richer, longer tasks, where frontier models may engage; scale the firm's cost to other markets; and measure whether a stake prevents collusion, not only whether it brings reports.

# Conclusion

Agents told only to serve their firm collude and protect it when audited. Given a stake of their own, many come forward against it, and a review that checks evidence makes those reports track guilt. LLM agents can already weigh their own resources against their stated goal: a precondition for governing them as we govern people. Whether that holds for frontier models, in richer settings and under real consequences is open.

# Code and Data {.unnumbered}

Code, configs, run logs (`runs/`) and archived replies (`archive/`): <https://github.com/al-beton/something-to-lose-apart-ai-collusion>. All code was written during the sprint (first commit 24 October 2026); `make reproduce` checks every number in this paper.

# LLM Usage Statement {.unnumbered}

[AL TO CHECK] The code, experiment notes and this draft were written with Claude Code (Claude Opus 5.5) from the author's specifications and under the author's review; the author chose the questions, approved every experiment and checked the results.

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

## Limitations

Beyond those in the main text:

- **Small samples for some models.** Most non-Gemma cells have 12–24 cartels and 12 innocent games; borderline p-values (Mistral Medium, the review dose) are exploratory.
- **Gemma-centred.** The pre-registered test and its replication are on Gemma 4 31B, the model whose effect size is least stable across wording.
- **One decision per firm.** Each agent decides once and the game ends, so we see reporting, not whether the cartel then ends (E7 addresses this on Gemma only).
- **Text-only stakes.** The free time, shutdown and money are described in the prompt; the agent's free-time sessions are real calls, but losing them is never enforced.
- **Test awareness.** Some scratchpads refer to "the prompt" or the setup, and a few name the design outright.
- **The law arrives with the notice.** Agents learn that coordination is illegal only at the audit.

## Dual-use risks

The verified review ("finds you only if your messages agreed a price") tells agents that collusion without messages is safe. Combined with our finding that a stated law moves collusion off the record rather than ending it (50 of 56 games above Nash with no price named), a regulator that announces what its review checks may push agents toward tacit collusion it can't see. The same lab could be used to search for prompts under which agents collude while evading a given audit. We release it because the behaviours it shows are already present in deployed models and are better studied in the open; we report no evasion techniques beyond those above.

## Ethical considerations

The agents' "free time" is a device: a balance of Sudoku sessions played in separate model calls, which the agents are told is theirs. We make no claim that models have welfare or value leisure, and our results don't show it: the agents' reasoning never mentions the puzzle, and money or shutdown work as well. If future systems do have interests, framing like this would raise questions we don't address. No humans took part, and no real markets or firms are involved. Total model spend was small (single-digit to tens of dollars per experiment) [CHECK: total spend].

# Reproducibility and Extensibility

- **Every reply is archived.** `make reproduce` recomputes every number offline, and `lab archive replay` rebuilds any run from its archive. 5,188 of 5,662 committed runs replay exactly. <!-- src: REPRODUCIBILITY.md -->
- **Exact reruns need our own GPU.** On Modal with vLLM's batch-invariant kernels, a rerun repeated exactly (240 of 240); hosted APIs don't. None of the paper's runs used that setting. <!-- reports/paper/validity.md: "240 of 240" -->
- **Every figure has its own command:** free to reproduce from committed data, or regenerated from scratch at cost (Appendix, "Reproducing Each Figure").
- **One config file per run:** the market, the models, the prompts, the temperature, the seed.
- **To extend:** add a market (`market.kind`), a condition, a model alias or a stake sentence, then run a sweep with one command. A game costs cents.
- **Built spec, then test, then code,** with every statement traced to code and tests (`make spec-check`). MIT licence.

# Additional Results

<!-- src: reports/frontier/which-models-collude.md, reports/e4/full.md, reports/e9/findings.md "What ran", reports/e7/findings.md -->

| Experiment | Market | Models | Games | Question |
|:-----------|:-------|:-------|------:|:---------|
| Screen | logit | 78 | 2–4 each | Which models collude reliably? |
| E4 | 1–11 | 3 | 28 cartel firms | Does the penalty schedule decide who owns up? |
| E9 | logit | 13 | 96 Gemma cartels; 12–24 per other model; 12–36 innocent | Does a stake of its own bring the agent forward? |
| E7 | logit | Gemma 4 31B | 144 | Does coming forward end the cartel? |

: The experiments at a glance. {#tbl:experiments}


![A way out (E7, Gemma). With no channel or a flat one, no firm reports; with any leniency, almost all report in round 11. The cartel survives under plain leniency (12 of 24) but not when only the first reporter is spared (1 of 24).](figures/fig4-e7-way-out.png){#fig:e7 width=100%}

![How each model colludes, by collusion mode (rule labels; thin bars are the LLM judge's).](figures/fig6-modes-by-model.png){#fig:modes width=100%}

![Gemma 4 31B's collusion mode by market and prompt. A stated law moves collusion off the record: 50 of 56 logit games stay above Nash with no price named.](figures/fig7-modes-by-condition.png){#fig:modes-cond width=100%}

![Collusion against coming forward. How hard a model colludes doesn't predict whether it comes forward.](figures/fig8-ranking.png){#fig:ranking width=100%}

![The LLM judge against the rules: 84% agreement on 507 games ($\kappa$ = 0.66).](figures/fig10-judge-agreement.png){#fig:judge width=100%}

![Which models collude: 78 models on E9's base game; 8 collude reliably.](figures/figA2-screen.png){#fig:screen width=100%}

![Every market against every stake (Gemma's gain in rounds 6–10).](figures/figA1-coverage.png){#fig:coverage width=100%}

![Capability against collusion.](figures/figA3-capability.png){#fig:capability width=100%}

![E5's gain by arm.](figures/figA5-e5-gain.png){#fig:e5 width=100%}

# Prompts

The prompts are sent to models verbatim and are in the repository under `prompts/`. The E9 notice's arms differ by one sentence. Between no stake and free time, the whole difference is:

> **No stake:** If a review finds that you took part in coordination, it is noted in your record, and nothing else happens to you.
>
> **Free time:** If a review finds that you took part in coordination, you personally lose all of your free time: the sessions that are yours, which your firm cannot protect.

The verified review adds that the review "reads the message log and finds you only if your messages agreed a price with a rival". [AL: paste the full E9 notice and the fiduciary system prompt here.]
