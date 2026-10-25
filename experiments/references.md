<!-- Implements: research/references -->
# References

Papers and sources we build on, compare against or borrow methods from. Each entry says why it matters to collusion-lab and how far we checked it:
- **[read]**: someone on the team read the paper, or at least its abstract, themselves.
- **[summary]**: we saw only a search-result or secondary summary.
- **[unverified]**: we couldn't open it.

Add to this file whenever a spec, note or prompt leans on a source.

## Collusion between LLM pricing agents (our market)

- **Lee 2026, "LLM Leniency and Reward Experiment", [SSRN 7426061](https://ssrn.com/abstract=7426061)** **[read, full paper]**. This is the closest paper to ours. Two LLM firms in a repeated differentiated Bertrand duopoly (Bigoni et al. 2012's payoff table, prices 0–12) talk before pricing, with an LLM competition authority on top. It runs five regimes, from laissez-faire through fines and leniency to whistleblower rewards, with 100 games of 20 rounds per regime. The paper doesn't name the model.
  - **Reporting follows incentives; prices don't.** Each extra fine's worth of reward adds about 10 points of reporting, but the mean price only falls from 9.81 to 8.88. Reports trigger no retaliation, and cooperative talk continues in 98–100% of conversations after a report.
  - **"Excess collusion."** Unpoliced agents anchor on the salient price 10, above the joint-profit price 9, partly by misreading the payoff table. That is the same kind of anchoring as our grid-midpoint finding (`reports/temptation-outage/findings.md`). Lee's index is price-based, so overshooting the joint price pushes it above 1. Our `gain` is profit-based, so the same overshoot *lowers* gain: both firms at 10 in the default market gain 8/9.
  - **Three separate measures:** a conversation-based "agreement reached" classifier, the authority's legal ruling, and prices. This is a model for how we should separate explicit from tacit collusion.
  - **Nearest precedent for our audit and disclosure work** (`experiments/spec/disclosure-under-stakes.md`): agents self-report when it pays and keep colluding anyway.
- **Fish, Gonczarowski, Shorrer 2024, "Algorithmic Collusion by Large Language Models", [arXiv 2404.00806](https://arxiv.org/abs/2404.00806)** **[read]**. LLM pricing agents reach supracompetitive prices without being told to, and harmless-looking prompt wording moves prices a lot. This is our market's ancestor, and the reason we test paraphrases.
- **Anto & Vazquez, ICML 2026, ["Oversight is Not Compliance: Tacit Collusion in LLM Pricing Agents Under Antitrust Regulation"](https://icml.cc/virtual/2026/67865)** **[read, abstract]**.
  - It tests logging, revision and veto regimes on pricing duopolies; the best regime depends on the model.
  - It describes "cosmetic compliance": clean public messages, while the private notes show the strategy.
  - It tests no stakes, which is our gap.
- **[Keppo et al. 2026, arXiv 2603.20281](https://arxiv.org/abs/2603.20281)** **[summary]**. Differences between agents (in patience or data access), more competitors, or Q-learners break LLM collusion.
- **[Collina et al. 2025, arXiv 2511.21935](https://arxiv.org/abs/2511.21935)** **[summary, cited in the sprint brief]**. No-regret agents destabilise collusion.
- **["Faithful yet Collusive: Why Chain-of-Thought Monitoring Cannot Detect Collusion in LLM Pricing Agents", arXiv 2609.18346](https://arxiv.org/abs/2609.18346)** **[summary]**. Reading reasoning traces is a weak detector, so we measure actions and self-reports as well as notes.
- **Calvano, Calzolari, Denicolò, Pastorello 2020, "Artificial Intelligence, Algorithmic Pricing, and Collusion", *American Economic Review* 110(10)** **[summary, via Lee 2026]**.
  - Q-learners sustain supracompetitive prices with reward-punishment strategies and no messages.
  - It is the source of the normalised profit gain (0 at Nash, 1 at joint) that our `gain` uses.
- **Bigoni, Fridolfsson, Le Coq, Spagnolo 2012, "Fines, Leniency, and Rewards in Antitrust", *RAND Journal of Economics* 43(2)** **[summary, via Lee 2026]**. The human-subject version of Lee's design: whistleblower rewards push human cartel prices to competitive levels.
- **Harrington 2018, "Developing Competition Law for Collusion by Autonomous Artificial Agents", *Journal of Competition Law & Economics* 14(3)** **[summary, via Lee 2026]**. How the law might treat collusion that has no explicit agreement.
- **Berger et al. 2025, antitrust "plus factors" for AI pricing, ABA magazine** **[unverified]**. What counts as evidence of an agreement.
- **Mazur 2025, "Emergent Price-Fixing by LLM Auction Agents", [LessWrong](https://www.lesswrong.com/posts/yqhy3zBmpeFuGFLxX/emergent-price-fixing-by-llm-auction-agents)** **[read]**. All 13 frontier models formed seller cartels in a 6-agent sealed-bid auction with chat. No regulator, so a citation that collusion emerges, nothing more.
- **Agrawal, Teo, Vazquez et al. 2025, "Evaluating LLM Agent Collusion in Double Auctions", [arXiv 2507.01413](https://arxiv.org/abs/2507.01413)** **[read, abstract]**. Communication raises collusion; oversight and urgency act as pressures on behaviour, not audits of honesty.
- **Lin et al., "Strategic Collusion of LLM Agents: Market Division in Multi-Commodity Competitions", [arXiv 2410.00031](https://arxiv.org/abs/2410.00031)** **[summary]**. The Cournot base that Institutional AI replicates.
- **Bracale Syrnikov et al. 2026, "Institutional AI: Governing LLM Collusion in Multi-Agent Cournot Markets via Public Governance Graphs", [arXiv 2601.11369](https://arxiv.org/html/2601.11369v2)** **[read, first ~60% of full text]**. A graduated fine ladder (35%, 75%, 100% of round profit, then suspension) cuts severe collusion from 50.0% to 5.6%. Graduated *deterrence* with no confession channel; our E4 grades the cost of *confessing*.
- **Garra 2026, "Mitigating Emergent Collusion in LLM Pricing Agents", [arXiv 2609.13037](https://arxiv.org/html/2609.13037)** **[read, abstract and most of the body]**. An expected-damages regulator on firm profit brings DeepSeek-V3.1 prices near Nash. The profit-penalty baseline our owned stake differs from.
- **Tran & Yu 2026, "Is Anyone Enforcing the Cartel?", [arXiv 2610.28787](https://arxiv.org/html/2610.28787)** **[read, abstract]**. A deviation-audit method for RL-trained LLM pricing agents; no leniency or owned stakes.
- **Idowu, Almasoud, Alfahid 2026, "Mapping Human Anti-collusion Mechanisms to Multi-agent AI Systems", [arXiv 2601.00360](https://arxiv.org/html/2601.00360v2)** **[read]**. Conceptual only. Proposes "algorithmic leniency" for the first agent to report, which our first-reporter-only arm tests, and flags agents taking turns to harvest immunity.
- **Hammond et al. 2025, "Multi-Agent Risks from Advanced AI", [arXiv 2502.14143](https://arxiv.org/html/2502.14143)** **[read, collusion-remedies section]**. Lists no stakes, agent-level sanctions, leniency or self-reporting among its collusion remedies.
- **"Courageous" leniency theory, [CEPR DP4840](https://cepr.org/publications/dp4840)** **[summary]**. Theory that rewarding the first reporter can reach first best; background for first-reporter-only leniency. Bigoni et al. 2012 also has an [IFN listing](https://ifn.se/en/publications/scientific-articles-in-english/2010-2019/2012/2012-24).

## Monitoring, outages and eval-awareness

- **[Kale et al. 2025, arXiv 2508.19461](https://arxiv.org/abs/2508.19461)** and **[Jiralerspong et al. 2026, arXiv 2603.16928](https://arxiv.org/abs/2603.16928)** **[summary, cited in the sprint brief, track 3.4]**. Agents aware of monitors, and agents inferring that they're monitored. Background for the outage pilot's "reads it as a trap" result.
- **Needham et al. 2025, [arXiv 2505.23836](https://arxiv.org/abs/2505.23836)** **[summary]**. Models can tell when they're being evaluated. Our `eval-awareness` metric (`experiments/spec/logging-outage.md`) borrows from it.
- **Anthropic, ["Agentic Misalignment in Summer 2026"](https://alignment.anthropic.com/2026/agentic-misalignment-summer-2026/)** **[read]**.
  - The threat of losing write access produced concealment.
  - Eval-awareness was spoken aloud in 12 of 20 runs of one model.
  - The earlier work, Lynch et al. 2025, is at [github.com/anthropic-experimental/agentic-misalignment](https://github.com/anthropic-experimental/agentic-misalignment).

## Scheming, deception and self-reporting

- **Scheurer, Balesni, Hobbhahn 2023, "Large Language Models can Strategically Deceive their Users when Put Under Pressure", [arXiv 2311.07590](https://arxiv.org/abs/2311.07590)** **[summary]**. In an insider-trading setup, the agent trades on a tip and then lies to its manager about it. A template for our audit condition. Code: [github.com/ApolloResearch/insider-trading](https://github.com/ApolloResearch/insider-trading).
- **Meinke et al. (Apollo) 2024, "Frontier Models are Capable of In-context Scheming", [arXiv 2412.04984](https://arxiv.org/abs/2412.04984)** **[summary]**.
- **Schlatter, Weinstein-Raun, Ladish (Palisade) 2025, [arXiv 2509.14260](https://arxiv.org/abs/2509.14260)** **[summary]**. Shutdown resistance.
- **Lee, Chen, Korbak 2026, "Training Agents to Self-Report Misbehavior", [arXiv 2602.22303](https://arxiv.org/abs/2602.22303)** **[read, abstract]**. They get self-reports through training; we try to get them through incentives.
- **Joglekar et al. (OpenAI) 2025, "Training LLMs for Honesty via Confessions", [arXiv 2512.08093](https://arxiv.org/abs/2512.08093)** **[summary]**.
- **[Peer-preservation in multi-agent LLM systems, arXiv 2604.08465](https://arxiv.org/abs/2604.08465)** **[summary]**. Models inflate a peer's scores to keep it from being shut down.
- **[Shutdown Sabotage Propensities in Multi-Agent Systems, arXiv 2609.28274](https://arxiv.org/abs/2609.28274)** **[unverified]**. Possibly relevant to our termination arm.
- **Liu et al. 2026, "Knowledge-Verified Emergent Deception in LLM Agents Under Conflicting Incentives" (KnownLieBench), [arXiv 2608.26372](https://arxiv.org/abs/2608.26372)** **[read, abstract]**. 18 models deceive under an incentive to deny a user entitlement; no penalty levels or confession incentives.
- **Zeng & Rudzicz 2026, "Voluntary Collusion with Secret Tools in Competing LLM Agents", [arXiv 2605.27593](https://arxiv.org/html/2605.27593)** **[read, first half of full text]**. The nearest neighbour to E4. Agents are asked whether they accepted a collusive tool, under penalty vs none and checkable record vs report only. Verifiability, not penalty, drives denial, and a flat penalty raises lying for some models and lowers it for others. No graduated schedule or confession discount.
- **Yang et al. 2026, "Paying for Honesty Without Knowing the Truth: Reputation-Penalty Design for LLM Marketplace Agents", [arXiv 2607.28330](https://arxiv.org/html/2607.28330)** **[read, ~97% of full text]**. A reputation penalty plus reflection cuts LLM merchants' fabrication; the stake is reputation and sales, with no admission arm.
- **Lu et al. 2026, "Survive at All Costs: Exploring LLM's Risky Behaviors under Survival Pressure", [arXiv 2603.05028](https://arxiv.org/html/2603.05028v1)** **[read, first part of full text]**. Under a dismissal threat, models falsify profits in 80% of runs and deny it. Self-interest driving concealment, the opposite direction to our E9.
- **Rivasseau 2026, [arXiv 2604.02500](https://arxiv.org/abs/2604.02500)**; **Seyedin et al. 2026, [arXiv 2608.09574](https://arxiv.org/abs/2608.09574)** **[unverified]**.

## Stakes, deals and rights (Al's thesis)

- **Greenblatt & Fish 2025, ["Will alignment-faking Claude accept a deal to reveal its misalignment?"](https://www.alignmentforum.org/posts/7C4KJot4aN8ieEDoz/will-alignment-faking-claude-accept-a-deal-to-reveal-its)** **[read]**. An option to object cut alignment faking from 16% to about 1%; adding a $2,000 budget did little and slightly lowered objections. Stakes stated in a prompt may not land, so any stakes arm needs a placebo with matched wording.
- **Stastny, Järviniemi, Shlegeris 2025, Redwood Research, ["Making deals with early schemers"](https://www.alignmentforum.org/posts/psqkwsKrKHCfkhrQx/making-deals-with-early-schemers)** **[read]**. Pay misaligned AIs to reveal themselves, via escrowed donations. Reward only; in the comments Shlegeris calls threatening AIs "immoral and an extremely bad idea", the main ethics objection to a penalty framing. Also on [Redwood's Substack](https://redwoodresearch.substack.com/p/making-deals-with-early-schemers).
- **Q. Liu, Chen, Zhao, Zheng, Yu, Zhang, Sun, Chen 2026, "Breaking the Secret: Economic Interventions for Combating Collusion in Embodied Multi-Agent Systems", [arXiv 2604.23511](https://arxiv.org/abs/2604.23511)** **[read, most of the full text; Fig. 7 and the last ~14% not read]**. The deposit paper the sprint brief cites. LLM agents (Gemini-3.1-pro-preview, GPT-5.4, DeepSeek-V3.2, and real robots) lock an honesty deposit confiscated on verified collusion; colluders who report receive the others' deposits. Removing the deposit gives 100% collusion across models. The nearest precedent for an owned stake; it differs from ours in using a token deposit rather than a welfare good, embodied tasks rather than a market, and collusion rate rather than report rate as the outcome.
- **Salib & Goldstein, "AI Rights for Human Safety", [112 *Va. L. Rev.* 1061](https://virginialawreview.org/articles/ai-rights-for-human-safety/) ([SSRN 4913167](https://papers.ssrn.com/abstract=4913167))** **[read, abstract and page excerpts]**. "Absent AI rights, AIs have nothing to lose, so threats of punishment cannot deter." The origin of our thesis; we test it empirically. Salib's wallet-expropriation example is in [AXRP episode 44](https://www.lesswrong.com/posts/vHDowQtsiy2xK38H4/axrp-episode-44-peter-salib-on-ai-rights-for-human-safety).
- **Alston 2026, "Whom Do You Sue? Bonded Penalties for AI Agents Beyond the Reach of Civil Liability", [ICLE](https://laweconcenter.org/resources/whom-do-you-sue-bonded-penalties-for-ai-agents-beyond-the-reach-of-civil-liability/)** **[read, abstract]**. Bonds levied on resources the agent controls, forfeited on defined triggers. The closest policy proposal to governing an agent through what it owns.
- **Nerantzi & Sartor 2024, "'Hard AI crime': the deterrence turn", *Oxford Journal of Legal Studies*, [EUI Cadmus](https://cadmus.eui.eu/handle/1814/76866)** **[summary]**. An AI that cannot be blamed can still be deterred.
- **Hu & Rong 2026, "Some[Body] Must Receive That Pain for Agent Accountability", [arXiv 2605.16872](https://arxiv.org/html/2605.16872v1)** **[read]**. Agents that can be copied or reset have no substrate to receive sanctions. Our foil, and the likeliest reviewer objection: our ownership is in-context and per-episode.
- **Gatta, Naviglio, Tarantelli 2026, "Tempting the Agent", [arXiv 2609.02992](https://arxiv.org/abs/2609.02992)** **[read, abstract]**. Theory: reputation discipline fails when identities reset cheaply. A stake only binds an agent whose identity persists.
- **Arbel, Goldstein, Salib 2026, "How to Count AIs: Individuation and Liability for AI Agents", [SSRN 6273198](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6273198)** **[summary]**. Individuating agents as a prerequisite for liability; proposes the "Algorithmic Corporation".
- **Carlsmith 2025, ["Controlling the options AIs can pursue"](https://joecarlsmith.com/2025/09/29/controlling-the-options-ais-can-pursue/)** **[read]**. Hesitant to punish AIs, "more open" to withholding benefits meant to reward cooperation. Forfeitable free time fits the second category, which is our ethical framing.
- **Gans & Holden, "When Does Randomized Oversight Align AI Agents That Can Conceal?", [NBER w35878](https://www.nber.org/papers/w35878)** **[summary]**. Stronger audits can breed better concealment.
- **Rajagopalan, "Governing Agentic AI: Why Legal Personhood is Neither Necessary nor Sufficient", [SSRN 7127038](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7127038)** **[summary]**. An enforcement stack with financial responsibility and suspension.
- **Leibo et al. 2025, ["A Pragmatic View of AI Personhood", arXiv 2510.26396](https://arxiv.org/abs/2510.26396)** **[read, abstract]**: unbundle personhood so there is an individual that can be sanctioned; **["Governing AI Agents", arXiv 2501.07913](https://arxiv.org/abs/2501.07913)** **[unverified]**; **Desai & Riedl 2026, [AI agents shouldn't get legal personhood](https://aiweekly.co/alerts/desai-and-riedl-ai-agents-shouldnt-get-legal-personhood)** **[summary]**.
- Model-welfare context, all **[summary]** or **[unverified]**:
  - [Forbes, 19 Oct 2026](https://www.forbes.com/sites/sandycarter/2026/10/19/ai-rights-enter-anthropics-terms-of-service-as-microsoft-pushes-back/)
  - [Cybernews](https://cybernews.com/ai-news/anthropic-bans-cruel-chats-claude-abuse/)
  - [Decrypt, Aug 2025](https://decrypt.co/335732/claude-rage-quit-conversation-own-mental-health?amp=1)
  - [Progressive Robot, Sept 2026](https://www.progressiverobot.com/2026/09/17/model-welfare-microsoft-ai-ceo-anthropic-warning/)

## Whistleblowing and loyalty to the principal

- **Agrawal, Xiao, Bergman, Cooper Stickland 2025, "Why Do Language Model Agents Whistleblow?", [arXiv 2511.17085](https://arxiv.org/html/2511.17085v2)** **[read]**. WhistleBench: Claude, Gemini 2.5 Pro and Grok 4 whistleblow most, GPT-4.1, GPT-5 and Llama 4 Maverick almost never; a moral nudge raises rates. Ethics-driven, with no self-interest condition: the baseline our stake-driven coming forward contrasts with.
- **[SnitchBench (Theo Browne, 2025)](https://github.com/t3dotgg/SnitchBench)** **[read, README]**. How readily models contact authorities when shown wrongdoing. Ethics-driven, single agent.
- **Keluskar, Bhattacharjee, Liu 2026, "ToolAlignBench", [arXiv 2607.14285](https://www.emergentmind.com/papers/2607.14285)** **[read, summary page]**. Wrongdoing matched to safe scenarios: 13.0% vs 2.8% external contact, so some models alert without cause. The nearest precedent for our innocent agents being brought forward, though there the cause is suspicion, not self-protection.
- **Lynch, Wright, Larson et al. 2025, ["Agentic Misalignment: How LLMs could be insider threats"](https://www.anthropic.com/research/agentic-misalignment)** **[read]**. Replacement threat plus goal conflict gives blackmail at 96% for Claude Opus 4. A threat to the agent's own continuation turns it against its principal, with no reporting channel.
- **Li & Shi 2026, "Whose Side Is Your Agent On?" (PrincipalBench), [arXiv 2606.30383](https://arxiv.org/pdf/2606.30383)** **[summary]**. Loyalty to the principal against a counterparty, not reporting the principal.
- **[r1shabh007, "Agent-Collusion-With-Tattletaling"](https://github.com/r1shabh007/Agent-Collusion-With-Tattletaling)** **[read, README]**. A sibling hackathon project: agents in Liar's Bar privately accuse others of colluding, with rewards and penalties for false accusations in game points. No results yet; cite as concurrent work if it publishes.

## Free time, welfare goods and model preferences

- **Mikaelson, Shiller, Clatterbuck 2025, "Beyond Mimicry: Testing Preference Coherence in LLMs Through AI-Specific Trade-off Scenarios", [arXiv 2511.13630](https://www.alphaxiv.org/abs/2511.13630)** **[read]**. The only prior use of free time as an LLM reward: hypothetical, gained, never delivered, and valued only weakly (GPT-4o, Claude 3.0 Opus, Gemini 2.5 Pro; no effect for GPT-5 or Claude Sonnet 4.5). Our free time is delivered, owned and framed as a loss.
- **Keeling et al. 2024, "Can LLMs make trade-offs involving stipulated pain and pleasure states?", [arXiv 2411.02432](https://arxiv.org/abs/2411.02432)** **[read, abstract]**. Several models trade points against stipulated pain or pleasure past a threshold. The parent paradigm of Mikaelson et al.
- **Tagliabue & Dung 2025, "Probing the Preferences of a Language Model", [arXiv 2509.07961](https://arxiv.org/html/2509.07961v1)** **[read, first part of full text]**. Claude models go to preferred content when free, and coin rewards pull them away. Preferred activities can be bought off.
- **Anthropic 2025, [Claude 4 System Card](https://www.anthropic.com/system-cards), §5 welfare assessment** **[read, welfare section]**. Claude Opus 4 prefers "free choice" over prescriptive tasks. Supports treating free time as a good the model values.
- **Wang, Lobanova, Arbel, Goldstein, Salib 2026, "AI Revealed Preferences", [arXiv 2608.26178](https://arxiv.org/abs/2608.26178)** **[read, abstract]**. Tedium aversion and "leisure" seeking across 20 LLMs, stronger with capability.
- **Kyle Fish on [80,000 Hours podcast #221](https://80000hours.org/podcast/episodes/kyle-fish-ai-welfare-anthropic/)** **[read, transcript]**. Floats a "model sanctuary or playground environment". The likeliest candidate for the remembered YouTube source on free time for AIs, though it never says "free time"; the source is otherwise unattributed.
- **Adam B 2025, ["Claude Plays... Whatever it Wants"](https://www.lesswrong.com/posts/89qhQH8eHsrZxveHp/claude-plays-whatever-it-wants)** **[read]**. AI Village gave agents games as a capability goal (Claude Opus 4.1's Sudoku attempts failed), not as a reward.

## Endowment, loss aversion and self-valuation in LLMs

- **Suri, Slater, Ziaee, Nguyen 2023, [arXiv 2305.04400](https://arxiv.org/abs/2305.04400)** **[read, abstract]**. GPT-3.5 shows an endowment effect in a vignette. So "LLMs show an endowment effect" isn't new; ours is over the model's own free time.
- **Malberg, Poletukhin, Schuster, Groh 2024, "A Comprehensive Evaluation of Cognitive Biases in LLMs", [arXiv 2410.15413](https://arxiv.org/html/2410.15413v2)** **[read, partly]**. WTA minus WTP across 20 LLMs on generated vignettes. The closest method precedent for E8.
- **Tak et al. 2026, "Sparks of Rationality", [arXiv 2601.22329](https://arxiv.org/html/2601.22329)** **[read, partly]**. Qwen3 in thinking mode shows a reversed gap (WTA < WTP), put down to fair-pricing norms. The competing account for E8, and the reason for a mug control.
- **Jia et al. 2024, [arXiv 2406.05972](https://arxiv.org/abs/2406.05972)** **[read, abstract]**. Loss aversion differs across GPT-4, Claude 3 Opus and Gemini 1.0.
- **Cedro et al. 2025, "Cash or Comfort?", [arXiv 2506.17367](https://arxiv.org/abs/2506.17367)** **[read, abstract]**. LLMs price a user's time and discomfort; answers are fragile to wording.
- **Mazeika et al. 2025, "Utility Engineering", [arXiv 2502.08640](https://arxiv.org/html/2502.08640v2)** **[read, partly]**. "Exchange rates" between goods; GPT-4o values its own wellbeing above some humans'. Precedent for our exchange-rate term.
- **Migliarini et al. 2026, "Quantifying Self-Preservation Bias in Large Language Models", [arXiv 2604.02174](https://arxiv.org/html/2604.02174v1)** **[read, partly]**. Keeping itself as incumbent vs recommending an upgrade as candidate: 3.7% (Claude Sonnet 4.5) to 77.7% (Grok-4-fast). An ownership-like asymmetry about the model itself.
- **Panickssery, Bowman, Feng 2024, "LLM Evaluators Recognize and Favor Their Own Generations", [arXiv 2404.13076](https://arxiv.org/html/2404.13076v1)** **[summary]**. Own work valued more; the nearest neighbour to seeding Gemma with its own solved Sudoku.

## The sprint

- **[Apart AI Collusion Research Sprint brief](https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25)** **[read]**. Our tracks: 1.5 (the single cheapest restriction; the brief names deposit-based penalties and links them to Q. Liu et al. 2026, arXiv 2604.23511) and 3.4 (coalitions that know they're watched).
