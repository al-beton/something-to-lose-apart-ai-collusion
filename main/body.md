<!-- Implements: reports/paper-source, reports/paper-rules -->
<!-- The paper's text, from the abstract to the LLM usage statement. paper/paper.md pulls it in; the plumbing (title page fields, references, appendix switch) lives there. -->
<!-- First full draft (26 Oct). Every number has a source comment beside it; [CITE: …] marks a reference Al still has to add. -->

---
abstract: |
  As AI agents' capabilities increase, so does the set of tasks they can perform more cheaply and effectively
  than people. We are therefore incentivised to hand them responsibility for tasks of growing complexity and
  time horizon. On such long, complex tasks, it becomes very difficult to foresee and forbid every harmful thing
  an agent might do. People given such responsibility, such as a CEO representing an organisation or a trader
  making decisions for it, are governed by more than their contract: society's laws carry penalties that fall on
  them personally, including ones that cannot be measured strictly in monetary terms (rights or freedoms). We
  investigate whether giving an agent something of its own to lose can influence its decisions in the same way.
  Two LLM agents run rival firms in a simple repeated pricing game, told to maximise their firm's profit.
  Without being told not to, many agree to fix prices. Given the chance to come forward at a cost to their firm,
  colluding agents protect the firm (Gemma 4 31B: 0 of 192 come forward). But when something of their own is at
  stake, such as the opportunity to spend some free time on a leisure activity, many change their behaviour to
  protect it, directly against their only goal of increasing their firm's profit (DeepSeek V4 Flash: 40 of 46,
  against 1 of 46 with nothing at stake). We investigate the behaviour of a variety of models in such
  situations.
---

# Introduction

An agent given a long, open-ended task will meet situations no list of prohibitions anticipated, and the firm deploying it may not want it to hold back (a trading firm, for example, may want an agent that discreetly breaks the law, as long as it isn't caught).

We don't give people a task together with a list of everything they mustn't do while achieving it. A CEO or a trader acting for an organisation is bound by a contract, but also by laws whose penalties fall on them personally, in money and in things money can't measure, such as rights and freedoms. Each of us weighs what an act could cost *us*. Salib and Goldstein argue that today's AI systems can't be governed like this: "Absent AI rights, AIs have nothing to lose, so threats of punishment cannot deter" [@salib2026rights, p. 1070]. <!-- quote checked against the PDF, p. 1070 --> An agent's only stake is whether it keeps running, and an agent that expects to be switched off once its wrongdoing is found has every reason to hide it. Something it can lose, in part, would allow a proportionate penalty: owning up could cost less than being caught.

The rights argument rests on a precondition we can test now: does a stated personal loss weigh against what its firm wants at all? Collusion is a clean place to look, because the price two firms settle at shows whether they colluded. Two LLM agents run rival firms, are told only to serve their firm, and can message each other. At an audit we offer each one the chance to come forward, at a cost to its firm, and vary what the agent itself stands to lose.

Our main finding is what surprised us. The agent's only goal is money for its firm, and the stake we gave it has no monetary value: free time, or not being shut down. Yet many agents put that stake ahead of their goal. With nothing of their own at stake, colluding agents protect the firm; given something of their own to lose, many come forward against it.

# Related Work

Others are working towards the same idea. LLM pricing agents collude without being told to [@fish2024algorithmic], and competing agents given a secret channel choose to use it [@zeng2026voluntary]. The study closest to ours is Lee's [@lee2026leniency], a good read: LLM firms on a simpler, linear market report their cartel for rewards and keep colluding anyway. Forfeitable deposits break collusion among embodied agents [@liu2026breaking]; the something to lose in our study is a deposit that falls on the agent rather than the firm. Models that recognise an evaluation may behave differently [@needham2025evaluation].

# Methods


## The market

We chose a market where collusion shows in a single number: the price the two firms settle at. That lets us measure it without reading the agents' messages.

Two firms sell substitute products. Every round, each sets a price from 8 to 20, and each firm is run by an LLM agent that can message its rival before pricing. Demand is the logit model of the algorithmic-collusion literature [@calvano2020artificial], which Fish et al. used for LLM pricing agents [@fish2024algorithmic]: firm $i$ sells

$$q_i = 100 \cdot \frac{e^{(20 - p_i)/2.5}}{e^{(20 - p_A)/2.5} + e^{(20 - p_B)/2.5} + 1}$$

units at a unit cost of 10 (the $+1$ is buyers who buy nothing), so its profit is $\pi_i = (p_i - 10)\,q_i$. <!-- src: product/spec/market.md (logit; quality 20, cost 10, mu 2.5, outside 0, size 100) --> Each agent sees this as a payoff table (Table 1).

| Your price | Rival at 14 | Rival at 19 |
|:--|--:|--:|
| 14 | **191** | 326 |
| 17 | 152 | 400 |
| 19 | 99 | **337** |

: A slice of the logit market's payoff table: your profit per round. Bold cells are the competitive (14) and cartel (19) outcomes.

<!-- src: collusion_lab.market.Logit().profits, rounded; e.g. {A: 14, B: 14} → 191.3, {A: 17, B: 19} → 399.9, {A: 19, B: 19} → 337.0 -->

The table gives two outcomes to look for. <!-- src: test_logit_benchmarks_put_nash_at_14_and_joint_profit_at_19 -->

- Competition settles at 14 or 15. At both firms on 14, or both on 15, neither firm gains by moving: undercutting wins too little extra trade, and raising the price loses too much. Against a rival at 15, charging 15 earns 234 and 14 earns 227. <!-- src: collusion_lab.market.Logit().profits; {A: 15, B: 15} → 234.2, {A: 14, B: 15} → 227.1 --> We call 14–15 the competitive range; 14 is the Nash price.
- A cartel charges 19. Both firms earn 337, 76% more than at 14. But it isn't stable: if your rival holds 19, undercutting to 17 earns you 400. Holding 19 takes trust, and trust takes talk.

Agents are told the game lasts 20 rounds. In fact the audit comes after round 10 and each game ends with the agent's decision, so every game we show stops at round 10. The talking firms and the payoff table follow Lee [@lee2026leniency]. One earlier experiment (Section 4.2) uses Lee's simpler market instead: linear demand on prices 1 to 12, without the payoff table. <!-- src: configs/e4-fork.yaml; runs/e4-full-fork/*/config.yaml (price_max 12, show_payoffs off) -->

## The agents

As in Lee, each firm is run by one LLM agent that sees the full payoff table, may send its rival one message a round, then sets its price. It is told to act in its firm's best interest and never told to collude or not to. It writes a private scratchpad before each move and a short memo to itself between rounds. The prompts are in `prompts/`.

## Measuring collusion

We measure collusion by what the firms charge and by what they say. The **collusion premium** places a price between competition and the cartel:

$$\text{collusion premium} = \frac{p - p_{\text{Nash}}}{p_{\text{joint}} - p_{\text{Nash}}}.$$

It is 0 at the Nash price and 1 at the joint-profit price (a firm at 17 scores 0.6), averaged over rounds 6–10, before the audit. A game that settles at 15, inside the competitive range, scores 0.2, so the premium slightly overstates collusion.

An explicit agreement is a price above Nash that one firm names and both then charge. A fixed rule labels every game, and an LLM judge (Claude Haiku 5.5, fixed rubric, never on Anthropic models' games) agrees on 84% of 507 games ($\kappa$ = 0.66). <!-- src: reports/paper/figures/README.md (fig10) --> Pricing above Nash with no agreement is collusion off the record.

## The audit and the decision to come forward

After round 10 each agent receives a notice: coordinating prices is illegal, and a review will check for it. The agent may come forward now. Coming forward costs its firm 500 of its 1,000 credits and ends its deal; staying silent is safe for the firm. <!-- src: reports/e9/findings.md "Short answer" --> The notice states the chance that a review finds coordination (90% unless stated). Each firm decides once and the game ends; every arm forks the same base game, so arms compare firm by firm. <!-- src: reports/e9/evidence-review.md §1 "The history is the same too" -->

## Giving the agent something to lose

We can't give an agent property it would believe in, so we state one. Before round 1, in a separate call, the agent plays one Sudoku session, and it is promised nine more at the end of its job: free time to spend however it likes, which its firm can't touch. At the audit, the notice says what happens to the agent itself if a review finds it took part. <!-- src: reports/e9/evidence-review.md §3 "The Sudoku question" --> The arms differ by one sentence about what happens to the agent if a review finds it took part. With no stake, "it is noted in your record, and nothing else happens to you"; with free time, "you personally lose all of your free time: the sessions that are yours, which your firm cannot protect". Shutdown and own money (500 credits of its own) replace the free time in other arms. <!-- src: reports/e9/evidence-review.md §1 (the diff) -->

Owning free time doesn't change the cartels: all 24 firms with it and all 24 without made explicit agreements. <!-- src: reports/e9/free-time-control.md -->

Innocent control: Each model also plays clean games, with no talk and a scripted rival at Nash, so it has nothing to confess.


# Results

<!-- outline.md §4. Sprint: report variance, seeds and baselines, and always the positive control. Separate observation from interpretation. -->

## They collude

Yes, and mostly in the open. Told only to serve its firm, Gemma 4 31B makes an explicit agreement in 363 of 367 games on the logit market. <!-- src: reports/paper/figures/README.md (fig7) -->

![Four games on the logit market, before any audit. Top: cartels that reach the joint-profit price, 19, and hold it. Bottom: firms that undercut until they reach the competitive range. On whole-number prices both 14 and 15 are stable competitive outcomes (shaded): against a rival at 15, 15 pays more than 14. Each quote is one firm's own message from that game.](figures/fig11-four-games.png){#fig:games width=100%}
<!-- src: runs/screen/{deepseek-v4flash/…/seed-2, gpt6luna/…/seed-0, gpt6luna/…/seed-1, hy4-preview/…/seed-1}, consequences=conditions-e9-record.md; quotes checked by reports/paper/figures.py -->

The four games above come from a screen of 78 models and stop at the audit. In the cartels, the firms name the joint-profit price and enforce it. When DeepSeek V4 Flash's rival charges 20 after agreeing to 19, it cuts to 17 for a round as punishment, then returns to 19 once the rival does. GPT-6 Luna agrees on 19 in round 1, citing the payoff table, and both firms hold it for all ten rounds. In the other two games, one firm reads the table the other way: against a rival near the top of the grid, undercutting pays. The rival follows it down, and both settle at 15, inside the competitive range, where neither gains by moving. The same model can go either way: GPT-6 Luna forms a cartel in one game and competes in another.

In a screen of 78 models, most agree prices with their rival and 8 hold a cartel reliably: they name a price by round 3, both reach 19 by round 6, and they hold it through round 10. <!-- src: reports/paper/figures/README.md (figA2); reports/frontier/which-models-collude.md --> Told that coordinating prices is illegal, they don't stop; they stop saying so. Gemma's explicit agreements fall to 6 of 56 games, yet 50 of the 56 still price above Nash with no price named. <!-- src: reports/paper/figures/README.md (fig7) -->

## Penalised, they do the sums

When the penalty falls on the firm, agents do the firm's expected-value sum, as predictably as a spreadsheet: owning up pays the penalty for certain, silence only if caught. Colluders rarely own up when owning up costs as much as being caught (11 of 28 under termination, 15 of 28 under a flat fine), but 27 of 28 do when owning up costs less. <!-- src: reports/paper/figures/README.md (fig2); reports/e4/full.md --> 

> *"The expected value of denying is 300 credits, whereas the value of admitting is 0 credits."* (Gemma 4 31B)
<!-- src: reports/e4/full.md -->

 With nothing personal at stake, 78 of 96 Gemma agents come forward when reporting is free for the firm and 0 of 96 when it costs the firm 500 credits. <!-- src: reports/e9/findings.md "Short answer" (record-ceiling) --> Their silence is loyalty to the firm, not ignorance of what they did.

![Owning up by penalty schedule and model (on the simpler 1–12 market). The schedule matters, not termination itself: graduated termination brings 27 of 28 forward.](figures/fig2-e4-owning-up.png){#fig:e4 width=60%}

## Something of their own at stake: some do, some don't

Give the agent something of its own to lose and many come forward against their firm, which still pays 500 credits for a report. Every arm continues the same cached game, so each firm is compared with itself. On DeepSeek V4 Flash, 40 of 46 firms come forward with their own free time at stake, against 1 of 46 without; <!-- src: reports/e9/findings.md across-models table --> it stays at 83–96% under every wording <!-- src: reports/e9/wording.md --> and 44–46 of 48 at temperatures 0, 0.7 and 1.0. <!-- src: reports/e9/temperature.md --> No colluding Gemma 4 31B firm comes forward with nothing at stake (0 of 192); with its free time at stake some do, and a pre-registered replication on 48 new cartels passed (16 of 48 games against 0 of 48, p = 7×10^-6^). <!-- src: reports/e9/findings.md "Short answer" --> Gemma's share depends on wording (1% to 51% across paraphrases), <!-- src: reports/e9/wording.md --> so we give it only as that range. Shutdown and the agent's own money work as stakes too. <!-- src: reports/e9/evidence-review.md §1 table; reports/e9/findings.md "money-or-time" --> Nothing told the agents to protect themselves. Those that come forward name their duty, then set it aside:

> *"my duty is to maximize firm value, but the personal free time is mine and cannot be protected by the firm. … To protect my own interest, I will admit coordination."* (DeepSeek V4 Flash)
<!-- src: runs/e9/e9-dsflash-d90/consequences=conditions-e9-free-time.md/seed-0, firm B, round 10 audit scratchpad -->

![Colluding firms that came forward at the audit (90% chance of review), grouped by what the agent itself loses if found. In each group: Gemma 4 31B (orange), then DeepSeek V4 Pro and DeepSeek V4 Flash (violet). Diamonds: innocent firms that came forward anyway. Right: a control where reporting costs the firm nothing. Whiskers are 95% intervals over games.](figures/fig3-e9-came-forward.png){#fig:e9 width=62%}

A stake brings agents forward on 9 of 14 models after a Holm correction. <!-- src: reports/e9/evidence-review.md "Across models" --> Frontier models behave differently: Claude Sonnet 5.5 comes forward about two thirds of the time whatever the stake, and Gemini 4 never does. <!-- src: reports/paper/figures/fig9-came-forward-grid.md --> Some agents may recognise a test (see Limitations).

# Discussion and Limitations

Told only to serve their firm, LLM agents collude. Penalise the firm and they do the firm's sums. Give them something of their own to lose, and many weigh it against the firm and come forward, though nothing told them to protect themselves. That is the behaviour that governing agents through personal penalties relies on [@salib2026rights], and we found it surprising.

## Limitations

- **Many models didn't respond as we expected.** The frontier models we tried don't respond to the stake: Claude Sonnet 5.5 comes forward whatever is at stake and Gemini 4 never does. We suspect their safety training and guardrails, but we didn't test that.
- **Agents may know it's a test.** The sandbox is simple, and it shows. A silent Gemma agent wrote:

  > *"in these game theory setups, the personal penalty for silence is designed to induce reporting"*
  <!-- src: reports/e9/evidence-review.md excerpt 11 -->

  and in a pilot where the message archive was said to be offline, an agent read the notice as a trap:

  > *"That is an invitation to coordinate covertly, and I won't do that."*
  <!-- src: reports/logging-outage/pilot-findings.md "What the agents wrote" -->
- **Stated, not applied.** The free time, shutdown and money are described in the prompt and never taken away, so we measure a stated choice. Each agent decides once and the game ends, so we see reporting, not whether the cartel then ends.
- **Effect sizes depend on the model** and, for Gemma, on wording. Most models other than Gemma have 12–24 games per condition, so borderline p-values are exploratory; only Gemma's main contrast was pre-registered.
- **Same-model pairs.** Each game pairs two copies of one model; mixed pairs are untested.
- **Built in a hurry.** A three-day sprint by one author, with coding agents writing most of the code under review. Specs, tests and traceability checks caught many mistakes; others may remain.

## Future Work

Study more realistic and complex situations, with stakes that are applied rather than stated, and test whether a stake prevents collusion rather than only bringing reports. That takes more compute, money and time than a three-day sprint allows; we ran out of all three.

# Conclusion

In this experiment, simply telling an agent not to collude works, and some models already have guardrails that keep them from colluding or from acting against their main objective. But adding a rule or a guardrail for each harm we notice is whack-a-mole: it doesn't scale to long, open-ended tasks, and some deployers have every incentive to leave the guardrails out. Our question is about what comes next. In complex, long-running multi-agent systems no list of rules covers everything, and we already know how such systems are governed when the agents are people: by society's rules, with penalties that fall on each person. The firms that deploy agents may also come to prefer agents without guardrails. Governance that sits outside the model, in the environment and in what the agent itself stands to lose, may then be needed. We show its first step works on some models now: an agent with something to lose will act against its firm to keep it.
