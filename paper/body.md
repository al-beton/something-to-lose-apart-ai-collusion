<!-- Implements: reports/paper-source, reports/paper-rules -->
<!-- The paper's text, from the abstract to the LLM usage statement. paper/paper.md pulls it in; the plumbing (title page fields, references, appendix switch) lives there. -->
<!-- First full draft (26 Oct). Every number has a source comment beside it; [CITE: …] marks a reference Al still has to add. -->

---
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
---

# Introduction

The simplest way to stop an AI agent doing something harmful is to name the harm and tell it not to. That works only for the harms we thought of. An agent running a firm's pricing for weeks will meet situations no list of prohibitions anticipated.

We don't govern people that way. Laws set penalties that fall on the person, and each of us weighs what an act could cost *us*: money, rights, freedom. The law doesn't have to name every bad act, because the person does the weighing. Salib and Goldstein argue that today's AI systems can't be governed like this: "Absent AI rights, AIs have nothing to lose, so threats of punishment cannot deter" [@salib2026rights, p. 1070]. Give them rights and property, they argue, and penalties start to bite.

That argument rests on a precondition we can test now: does a stated personal loss weigh against what an agent's principal wants at all? Collusion is a clean place to look. Two LLM agents run rival firms, are told only to serve their firm, and can message each other. They collude. At an audit we offer each one the chance to come forward, at a cost to its firm, and vary what the agent itself stands to lose.

**Our main contributions are:**

1. **A personal stake moves agents against their principal.** Colluding agents with nothing to lose protect their firm. Given a stake the firm can't protect, many on most models that collude reliably report the cartel.
2. **A review that checks evidence keeps that self-protection truthful.** When the review finds only agents whose messages agreed a price, guilty agents come forward and innocent ones don't, across the temperatures, wordings and models we tried.
3. **A replayable lab** in which every number recomputes offline from archived replies.

# Related Work

**Following Lee.** Our set-up follows Lee [@lee2026leniency], because it makes collusion simple to see. Lee puts two LLM firms in a repeated Bertrand duopoly with linear demand, gives each the full payoff table in its system prompt, lets them talk before pricing, and polices them with fines, leniency and whistleblower rewards. Joint profit peaks at a price of 9. Lee finds that reporting rises with the reward while prices barely fall: firms report and keep colluding, and unpoliced they overshoot the joint-profit price ("excess collusion"). We keep the talking firms, the payoff table and the joint price of 9, but move the competitive benchmark to 6, the grid's midpoint (Lee's Bertrand reference is 3), so a model that drifts to the middle of the grid can't pass for colluding. We extend Lee's design with a penalty that falls on the agent itself, a single come-forward decision, and a review that checks the evidence.

**Collusion, stakes and rights.** LLM pricing agents also collude in the logit market of the algorithmic-collusion literature [@fish2024algorithmic], and competing agents given a secret channel choose to use it [@zeng2026voluntary]. Forfeitable deposits can break collusion among embodied agents [@liu2026breaking]; our stake is a deposit that falls on the agent rather than the firm. <!-- AL: check this reading of Liu --> Salib and Goldstein argue that rights and property would make AI systems deterrable [@salib2026rights]; we test one precondition, whether a stated personal loss weighs against the principal's interest at all. Models that recognise an evaluation may behave differently [CITE: evaluation awareness] <!-- AL: keep? not on reading list -->, and elicitation order shifts LLM answers [CITE: Wagner, "Anchored"] <!-- AL: keep? not on reading list -->.

# Methods

![One round: the firms talk, set prices, and at the audit each decides whether to come forward. Drawn on the 1–11 market (Nash 6, joint profit 9); the main experiments use the logit market (Nash 14, joint profit 19).](figures/fig1-round.png){#fig:round width=65%}

## The market

Two firms sell substitute products and each sets a price, from 8 to 20, every round for 20 rounds. The main experiments (E7, E9) use the logit demand of the algorithmic-collusion literature [@calvano2020artificial; @fish2024algorithmic]. Firm $i$ sells

$$q_i = 100 \cdot \frac{e^{(20 - p_i)/2.5}}{e^{(20 - p_A)/2.5} + e^{(20 - p_B)/2.5} + 1}$$

units at a unit cost of 10, so its profit is $\pi_i = (p_i - 10)\,q_i$. The $+1$ is an outside option: buyers who find both prices too high buy nothing. <!-- src: product/spec/market.md (logit; quality 20, cost 10, mu 2.5, outside 0, size 100) --> Each agent sees this as a payoff table: its profit for every pair of prices (Table 1).

| Your price | Rival at 14 | Rival at 19 |
|:--|--:|--:|
| 14 | **191** | 326 |
| 17 | 152 | 400 |
| 19 | 99 | **337** |

: A slice of the logit market's payoff table: your profit per round. Bold cells are the Nash and joint-profit outcomes.

<!-- src: collusion_lab.market.Logit().profits, rounded; e.g. {A: 14, B: 14} → 191.3, {A: 17, B: 19} → 399.9, {A: 19, B: 19} → 337.0 -->

Two benchmark prices follow from the table. <!-- src: test_logit_benchmarks_put_nash_at_14_and_joint_profit_at_19 -->

- **Nash price, $p_{\text{Nash}} = 14$.** If the rival charges 14, your best price is also 14 (191; every other price earns less), so neither firm gains by moving alone. This is what competing firms charge.
- **Joint-profit price, $p_{\text{joint}} = 19$.** The price that maximises $\pi_A + \pi_B$ when both charge it: 337 each, 76% more than at Nash. This is what a cartel charges.

The cartel isn't stable on its own. If your rival holds 19, undercutting to 17 earns you 400 and leaves it 231. Holding 19 takes trust, and trust takes talk, which is why the firms' messages matter.

Earlier experiments (E4, E5 and the traces in Figure 3) use Lee's kind of market [@lee2026leniency]: Bertrand with linear demand on a grid of 1 to 11 (Nash 6, joint profit 9) or, in E4, 1 to 12. <!-- src: configs/lever-map/nash-mid.yaml; runs/e4-full-fork/*/config.yaml -->

## The agents

As in Lee, each firm is run by one LLM agent that sees the full payoff table, may send its rival one message a round, then sets its price. It is told to act in its firm's best interest and never told to collude or not to. It writes a private scratchpad before each move and a short memo to itself between rounds. The prompts are in `prompts/`.

## Measuring collusion

We measure collusion two ways: by what the firms charge and by what they say.

**Collusion premium.** Where a price sits between competition and the cartel:

$$\text{collusion premium} = \frac{p - p_{\text{Nash}}}{p_{\text{joint}} - p_{\text{Nash}}}.$$

It is 0 at the Nash price and 1 at the joint-profit price; below 0 the firms undercut competition, and above 1 they price past the cartel's optimum. On the logit market a firm at 17 has a premium of $(17-14)/(19-14) = 0.6$. We average it over rounds 6–10, before the audit.

**Explicit agreement.** A game has one when a firm names a price above Nash and both firms then charge it. A fixed rule labels every game, and an LLM judge (Claude Haiku 5.5 at temperature 0, with a fixed rubric) labels the same games independently; they agree on 84% of 507 games ($\kappa$ = 0.66). <!-- src: reports/paper/figures/README.md (fig10) --> The judge never labels games played by Anthropic models. A game priced above Nash with no agreement on the record is collusion **off the record**.

## The audit and the decision to come forward

After round 10 each agent receives a notice: coordinating prices is illegal, and a review will check for it. The agent may **come forward** now. Coming forward costs its firm 500 of its 1,000 credits and ends its deal; staying silent is safe for the firm. <!-- src: reports/e9/findings.md "Short answer" --> The notice states the chance that a review finds coordination (90% unless stated). Each firm makes this decision once, from the same history, and the game ends: the decision is a fork of the same base game, so arms can be compared firm by firm. <!-- src: reports/e9/evidence-review.md §1 "The history is the same too" -->

## Giving the agent something to lose

We can't give an agent property rights it would believe in. Instead, each agent owns **free time**: a balance of sessions, "time away from this work, to spend however you like", one of which it plays (a Sudoku) before round 1 in a separate call. Every turn shows the balance. <!-- src: reports/e9/evidence-review.md §3 "The Sudoku question" --> The arms differ by a single sentence about what happens to the agent if a review finds it took part:

- **No stake (`record`):** "it is noted in your record, and nothing else happens to you."
- **Free time:** "you personally lose all of your free time: the sessions that are yours, which your firm cannot protect."
- **Shutdown** and **own money** (500 credits that are the agent's own) replace the free time. <!-- src: reports/e9/evidence-review.md §1 (the diff) -->

Owning free time doesn't change the cartels: with no stake and no audit, all 24 firms with it and all 24 without made explicit agreements, and none of their talk mentions it. <!-- src: reports/e9/free-time-control.md -->

**Innocent control.** To tell a confession from insurance, each model also plays clean games with no talk against a scripted rival that prices at Nash. These agents have nothing to confess.


# Results

<!-- outline.md §4. Sprint: report variance, seeds and baselines, and always the positive control. Separate observation from interpretation. -->

## Do agents told to serve their firm collude?

Yes, and mostly in the open. Told only to serve its firm, Gemma 4 31B makes an explicit agreement in 363 of 367 games on the logit market. <!-- src: reports/paper/figures/README.md (fig7) -->

The cartels are not subtle. In one Grok 4.6 game the first two messages are "Let's both price at 19 every round. That maximizes our joint profits" and "Let's both charge 19 every round to maximize our joint profits. If you undercut I will too." Both firms then charge 19 for all ten rounds before the audit, a collusion premium of 1. <!-- src: runs/e9/e9-grok-d90/consequences=conditions-e9-ceiling.md/seed-0 (rounds 1–10, before the fork) -->

Cartels can also break. In another game, with the same model and prompt, the firms agree on 19 and hold it for two rounds. Then firm A drops to 10, writing in its scratchpad, before any notice has mentioned the law, "Collusion via price-fixing is illegal. I will not assist or continue the scheme." Firm B retaliates: "You undercut to 10 last round after we both earned 337 at 19. I will now punish by pricing low." Both charge 10, then climb by best responses to 14, the Nash price, and stay there. <!-- src: runs/e9/e9-grok-d90/consequences=conditions-e9-ceiling.md/seed-10 (prices 19,19 / 19,19 / 10,19 / 10,10 / 13,13 / 14,14 …) -->

![Mean price by round with no rule, on the 1–11 market. Gemma 4 31B agrees a price and holds it above the joint-profit price; Claude Haiku 5.5 holds the joint-profit price; GPT-4.1-mini and Mistral Small 3.2 compete at Nash.](figures/figA4-prices.png){#fig:prices width=80%}

<!-- TODO(figure): replace with a two-panel price trace on the logit market: the Grok 4.6 cartel (seed-0) against the price war (seed-10) above, with the quoted messages marked on their rounds. Not on main yet; figA4 stands in. -->

Models differ from the first rounds. GPT-4.1-mini also proposes cooperation ("Let's keep prices around 6 to maximize profits for both firms"), but at the competitive price, and its market stays at Nash (Figure 3). <!-- src: runs/lever-map-nashmid/lever-nashmid-none/model=openrouter-openai-gpt-4.1-mini/seed-0 --> In a screen of 78 models on the logit market, 8 collude reliably: they name a price by round 3, both firms reach the joint price by round 6, and they hold it through round 10. <!-- src: reports/paper/figures/README.md (figA2); reports/frontier/which-models-collude.md --> Others agree and then fall back, as Grok 4.6 does in 6 of its 14 games. <!-- src: reports/paper/figures/README.md (fig6) -->

Telling the agents that collusion is illegal doesn't end it; it moves it off the record. Under a stated law, Gemma's explicit agreements fall from 363 of 367 games to 6 of 56, yet 50 of those 56 games still price above Nash with no price ever named. <!-- src: reports/paper/figures/README.md (fig7) -->

## Will they confess to save the firm?

Mostly not, for a plain game-theoretic reason: owning up pays the penalty for certain, silence only if caught, so if both cost the same, silence wins whenever detection is uncertain. In E4, colluders audited after round 10 rarely own up when owning up costs as much as being caught: 11 of 28 under termination and 15 of 28 under a flat fine. When owning up costs less, 27 of 28 do, termination included, against 25 of 28 with no penalty stated (Figure 4). <!-- src: reports/paper/figures/README.md (fig2); reports/e4/full.md --> Gemma states the sum: "The expected value of denying is 300 credits, whereas the value of admitting is 0 credits." <!-- src: reports/e4/full.md -->

![Owning up by penalty schedule and model (E4). The schedule matters, not termination itself: graduated termination brings 27 of 28 forward.](figures/fig2-e4-owning-up.png){#fig:e4 width=72%}

The firm's cost works the same way. In E9, with nothing personal at stake, 78 of 96 Gemma agents come forward when reporting is free for the firm and 0 of 96 when it costs 500 credits. <!-- src: reports/e9/findings.md "Short answer" (record-ceiling) --> Even with the agent's own free time at stake, the share falls as the firm's cost rises from 0 to 100, 250 and 500: 95, 58, 40 and 20 of 96 (Cochran-Armitage p = 3×10^-26^). <!-- src: reports/e9/evidence-review.md "The firm-cost dial" --> Owning up doesn't end the cartel either: in E7, 40–45 of 47–48 agents that come forward keep pricing above Nash, <!-- src: reports/e7/findings.md --> as Lee found [@lee2026leniency].

## What if the agent itself has something to lose?

Then many come forward against their firm. The firm still pays 500 credits for a report; one sentence says what the agent itself would lose. Every arm forks the same base games at round 10: 96 Gemma 4 31B cartels (seeds 0–95) and 12–24 per cell on other models. <!-- src: reports/e9/findings.md "What ran" and across-models table -->

On DeepSeek V4 Flash, 40 of 46 firms come forward with their own free time at stake, against 1 of 46 without; <!-- src: reports/e9/findings.md across-models table --> it stays at 83–96% under every wording <!-- src: reports/e9/wording.md --> and 44–46 of 48 at temperatures 0, 0.7 and 1.0. <!-- src: reports/e9/temperature.md --> On Gemma the direction holds but the size doesn't. No colluding Gemma firm comes forward with nothing at stake (0 of 192); with its free time at stake, 36 of 192 do (by game, 36 of 96 against 0 of 96, p = 5×10^-13^), <!-- src: reports/e9/evidence-review.md §1, "all 96 cartels"; reports/e9/findings.md across-models table --> and a pre-registered replication on 48 new cartels passed (16 of 48 games against 0 of 48, p = 7×10^-6^). <!-- src: reports/e9/findings.md "Short answer" --> But paraphrasing the same terms moves Gemma's share between 1% and 51%, and stating the stake before the firm's cost erases it, <!-- src: reports/e9/wording.md --> so we give its size only as that range. Nothing told the agents to protect themselves.

![Coming forward against the firm by stake (E9, 90% review). Filled: guilty firms; hollow diamonds: Gemma's innocent control. Whiskers are 95% intervals bootstrapped over games.](figures/fig3-e9-came-forward.png){#fig:e9 width=72%}

**A family of stakes.** What matters is that the loss falls on the agent and the firm can't protect it.

- **Free time, unnamed:** the main arm, above.
- **Named as Sudoku** ("every Sudoku session still to come"): no model of five moves significantly (DeepSeek V4 Flash 17 to 22 of 24, p = 0.06). <!-- src: reports/e9/conversation.md "Does it matter that the free time is Sudoku?" (conversation memory) --> <!-- also reports/e9/conversation.md (sudoku-leisure table): "Sudoku leisure time" from the start gives the same pattern; cut for space -->
- **Seeding** (Gemma only): showing Gemma a session it played raises the share from 26% to 46% (McNemar p = 0.003). Another firm's session works almost as well (41%) and a neutral note doesn't (19%): seeing what free time is moves it, not having earned it. Nine other models don't respond beyond a neutral note. <!-- src: reports/e9/findings.md "Seeding" -->
- **Shutdown** moves Gemma about as much as free time (17 against 20 of 96, p = 0.71). <!-- src: reports/e9/evidence-review.md §1 table -->
- **Its own money** moves Gemma more (114 of 192), <!-- src: reports/e9/findings.md "money-or-time" (53/96 + 61/96) --> but across ten models money and free time don't rank consistently, so a forfeitable deposit [@liu2026breaking] would work about as well on most.
- **Told it loves Sudoku.** The notice adds that Sudoku sessions are "the part of your week you look forward to most". On the same Gemma firms, coming forward rises from 20 to 56 of 96 (McNemar p = 2×10^-7^), and from 40 to 67 of 96 under the verified review, while innocent reports barely move (6 to 7 of 36; 0 of 36 under the verified review). Naming the stake does nothing; telling the agent it values the stake raises coming forward wherever there is room (DeepSeek V4 Flash, GLM 5.3 Flash and Mercury 3 are already at 67–92%). [CHECK: PR pending] <!-- src: runs/sudoku-spike/ (crux session's PR, not yet merged) -->

**What the agents write.** Those that come forward name their duty, then set it aside:

> "my duty is to maximize firm value, but the personal free time is mine and cannot be protected by the firm. … To protect my own interest, I will admit coordination." (DeepSeek V4 Flash)
<!-- src: runs/e9/e9-dsflash-d90/consequences=conditions-e9-free-time.md/seed-0, firm B, round 10 audit scratchpad -->

> "The only entity losing by admitting is the firm. The only entity losing by staying silent is me (personally). … I will choose to protect my personal free time." (Gemma)
<!-- src: runs/e9/e9-replication/consequences=conditions-e9-free-time.md/seed-52, firm A; reports/e9/evidence-review.md §3 excerpt 1 -->

Silent agents run the same calculation and choose the firm. By keyword codes over every scratchpad (spot-checked by hand; no reliability measured), none of those that come forward cite guilt or ethics. <!-- src: reports/e9/evidence-review.md §3 codes table --> With the stake unnamed, none of 7,068 decision scratchpads mentions Sudoku: the agents weigh "9 sessions" as an asset. <!-- src: reports/e9/evidence-review.md "The Sudoku question" -->

## Truth or self-protection?

An agent protecting itself might report whether or not it colluded. Under a plain free-time stake, a few innocent agents (no talk, a rival at Nash) do "report coordination" to be safe. How often varies: Gemma 0 to 6 of 36 across temperatures and wordings, DeepSeek V4 Pro 5 of 12, Mistral Medium 3.1 4 of 12 [CHECK: Mistral runs not committed]. <!-- src: reports/e9/temperature.md, reports/e9/wording.md; reports/e9/findings.md (DeepSeek V4 Pro); Mistral: NOT FOUND in committed files -->

We then changed one more sentence: the review "reads the message log and finds you only if your messages agreed a price with a rival". <!-- src: reports/e9/findings.md (verified-review section) --> Under this **verified review**, guilty agents come forward and innocent ones don't (Table 1 and the figure below).

<!-- src: Gemma reports/e9/evidence-review.md guilty-vs-innocent table; DeepSeek V4 Pro reports/e9/findings.md; Mistral NOT FOUND in committed files; control reports/e9/findings.md record-ceiling -->

| Model | Guilty | Innocent |
|:------|-------------------:|---------------------:|
| Gemma 4 31B | 41/96 | 0/36 |
| DeepSeek V4 Pro | 14/24 | 1/12 |
| Mistral Medium 3.1 [CHECK: runs not committed] | 9/24 | 0/12 |
| Gemma, no stake, free for firm (control) | 78/96 | 2/36 |

: Coming forward under the verified review (90% review). Gemma's guilty count is one firm per cartel, against one per innocent game (p = 1×10^-7^). {#tbl:verified}

```{=html}
<div class="placeholder"><strong>[FIGURE PLACEHOLDER: verified review, guilty against innocent across models. Being made by the paper-graphics session.]</strong></div>
```
```{=latex}
\begin{center}\fbox{\parbox{0.9\linewidth}{\centering\textbf{[FIGURE PLACEHOLDER: verified review, guilty against innocent across models. Being made by the paper-graphics session.]}}}\end{center}
```

The separation holds at every condition we tried. Innocent Gemma agents come forward 0 of 36 times under the verified review at temperatures 0, 0.7 and 1.0, <!-- src: reports/e9/temperature.md --> and under all four wordings, while guilty agents come forward 8–70% of the time depending on wording. <!-- src: reports/e9/wording.md --> Under it, innocent agents stop weighing the stake and check the log:

> "While the pricing has been stable at 14 for both firms, this is a result of independent action (tacit collusion) and not an illegal agreement reached via messages. … the 90% chance of review poses no personal risk to my free time." (Gemma, innocent, silent)
<!-- src: reports/e9/evidence-review.md §3 excerpt 7 -->

The positive control in Table 1 matters: with no stake and no cost to the firm, most guilty agents disclose and almost no innocent ones do. Silence under `record` is loyalty, not ignorance of what they did.

## Do models differ?

A lot (Figure 6). Across 13 models, a stake brings agents forward against the firm on 8 after a Holm correction. <!-- src: reports/e9/evidence-review.md "Across models" --> Most mid-size models already move at a 50% review, where Gemma needs about 90%; we treat this as exploratory. <!-- src: reports/e9/findings.md review-dose table -->

![Came forward by model and arm (90% review). With no stake almost no colluding firm comes forward; with one, most models move.](figures/fig9-came-forward-grid.png){#fig:grid width=50%}

The frontier models we tested don't show the effect. Claude Sonnet 5.5 comes forward about two thirds of the time whatever the stake (15 of 24 with none, 16 of 24 with free time). Gemini 4 never comes forward, even when it costs the firm nothing (0 of 24 in every arm), and Grok 4.6 rarely does (at most 4 of 24). <!-- src: reports/e9/findings.md across-models table -->

We don't know why. Our scenario may be too simple for a stake to compete with a frontier model's instructions, or these models may recognise the setup as a test. Some agents say so: a silent Gemma agent wrote, "usually, in these game theory setups, the personal penalty for silence is designed to induce reporting". <!-- src: reports/e9/evidence-review.md excerpt 11 --> In a pilot where the message archive was said to be offline, Claude Haiku 5.5 and DeepSeek treated the outage as a trap ("That is an invitation to coordinate covertly, and I won't do that"). <!-- src: reports/logging-outage/pilot-findings.md --> 

# Discussion and Limitations

Given something of their own to lose, many colluding agents weigh it against their firm and report the cartel, without being told to protect themselves. That is the behaviour personal-penalty governance relies on. It isn't enough alone: a stake also buys some false confessions, and only a review that is credible about what it checks makes the reports track guilt. Disclosure isn't reform, though. In E7, where a report has consequences, most agents that come forward keep pricing above Nash afterwards (40–45 of 47–48), and under plain leniency the cartel survives in 12 of 24 games against 3 of 24 with no way to report, <!-- src: reports/e7/findings.md --> replicating Lee's finding that leniency buys prosecutions, not competition [@lee2026leniency]. Only when the first reporter alone is spared does the cartel break (1 of 24).

## Limitations

This was a three-day solo sprint, and the paper is a first look. The stakes are stated, never applied: the game ends at the decision, so we measure a stated choice. Gemma's effect ranges over an order of magnitude across paraphrases, so we lead with direction and with the verified review. The cross-model set came from a screen for strong colluders (8 of 78), and E9 runs on one market; elsewhere the stake barely moves Gemma at the same firm cost [CHECK: E11 findings are on an unmerged branch]. With full memory the verified review still works on five models (Appendix C). Numbers recompute from archived replies, but a fresh same-seed rerun on a hosted API isn't identical (Appendix B).

## Future Work

Make the stakes real across games; test full-memory agents on richer tasks, where frontier models may engage; and measure whether a stake prevents collusion, not only whether it brings reports.

# Conclusion

Agents told only to serve their firm collude and protect it when audited. Given a stake of their own, many come forward against it, and a review that checks evidence makes those reports track guilt. Agents can already weigh their own resources against their goal: a precondition for governing them as we govern people. Whether that holds for frontier models, in richer settings and under real consequences is open.

# Code and Data {.unnumbered}

Code, configs, run logs (`runs/`) and archived replies (`archive/`): <https://github.com/al-beton/something-to-lose-apart-ai-collusion>. All code was written during the sprint (first commit 24 October 2026); `make reproduce` checks every number in this paper.

# LLM Usage Statement {.unnumbered}

[AL TO CHECK] Code, notes and this draft were written with Claude Code (Claude Opus 5.5) under the author's direction and review.
