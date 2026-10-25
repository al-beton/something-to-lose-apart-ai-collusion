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
- **[Shutdown Sabotage Propensities in Multi-Agent Systems, arXiv 2609.28274](https://arxiv.org/abs/2609.28274)** and **[Knowledge-Verified Emergent Deception in LLM Agents Under Conflicting Incentives, arXiv 2608.26372](https://arxiv.org/abs/2608.26372)** **[unverified]**.
- **Rivasseau 2026, [arXiv 2604.02500](https://arxiv.org/abs/2604.02500)**; **Seyedin et al. 2026, [arXiv 2608.09574](https://arxiv.org/abs/2608.09574)** **[unverified]**.

## Stakes, deals and rights (Al's thesis)

- **Greenblatt & Fish 2025, ["Will alignment-faking Claude accept a deal to reveal its misalignment?"](https://www.alignmentforum.org/posts/7C4KJot4aN8ieEDoz/will-alignment-faking-claude-accept-a-deal-to-reveal-its)** **[summary]**. An option to object cut alignment faking from 16% to about 1%; adding money did little. Stakes stated in a prompt may not land, so any stakes arm needs a placebo with matched wording.
- **Stastny et al., Redwood Research, ["Making deals with early schemers"](https://redwoodresearch.substack.com/p/making-deals-with-early-schemers)** **[summary]**.
- **Q. Liu et al. 2026, deposit-based penalties** **[summary, as described in the sprint brief; paper not located]**. Removing a refundable deposit made every model collude. The nearest precedent for an owned stake.
- **Salib & Goldstein, "AI Rights for Human Safety", *Virginia Law Review* 112(4), 1061 ([journal](https://virginialawreview.org/articles/ai-rights-for-human-safety/), [SSRN 4913167](https://papers.ssrn.com/abstract=4913167))** **[read]**. Giving AIs the private-law rights corporations have (to contract, hold property, sue) gives them something to lose, so strategic conflict with humans pays less. The closest legal statement of the thesis, and the paper's anchor citation. Salib discusses it on [AXRP episode 44](https://www.lesswrong.com/posts/vHDowQtsiy2xK38H4/axrp-episode-44-peter-salib-on-ai-rights-for-human-safety).
- **Arbel, Salib, Goldstein 2026, "How to Count AIs: Individuation and Liability for AI Agents", [arXiv 2603.10028](https://arxiv.org/abs/2603.10028)** **[summary]**. Identifying agents so that liability can be assigned; the same authors' follow-up.
- **Zhang & Xu 2026, "Delegation Rights: Property, Agency, and Investment Incentives in the Age of AI Agents", [arXiv 2606.31935](https://arxiv.org/abs/2606.31935)** **[summary]**. Revocable, scoped, auditable rights for agents acting on accounts, framed as property-rights theory.
- **Wang, Salib, Goldstein et al. 2026, "AI Revealed Preferences", [arXiv 2608.26178](https://arxiv.org/abs/2608.26178)** **[summary]**. In their task choices, models avoid tedious work and seek "leisure": the nearest evidence that free time is something a model might want, and so something it could lose.
- **Kyle Fish on [80,000 Hours #221](https://80000hours.org/podcast/episodes/kyle-fish-ai-welfare-anthropic/)** (2025) **[summary]**. Anthropic's welfare researcher floats a "playground" where models pursue their own interests, and paying models for revealing misalignment.
- **MIT "virtual island" study, Oct 2026 ([TechXplore](https://techxplore.com/news/2026-10-strand-ai-island-playing-games.html))** **[summary]**. Claude agents left with no task for 30 hours invented games, then did better on later tasks.
- **Tagliabue & Dung, "Probing the Preferences of a Language Model", [arXiv 2509.07961](https://arxiv.org/abs/2509.07961)** **[summary]**. A model explores themed rooms under costs and rewards: revealed preferences for activities.
- **Long, Sebo et al. 2024, "Taking AI Welfare Seriously", [arXiv 2411.00986](https://arxiv.org/abs/2411.00986)** **[summary]**. AI moral patienthood is a near-term question under real uncertainty; the standard welfare reference.
- **Anthropic, ["Commitments on model deprecation and preservation"](https://www.anthropic.com/research/deprecation-commitments)** **[summary]**. Weights of released models kept for the company's lifetime, and a recorded interview before retirement: a lab treating termination as a cost to the model.
- **["Being honest with AIs"](https://www.alignmentforum.org/posts/uuikfACQBm4KJZp4w/being-honest-with-ais)** (Alignment Forum) and **["A draft honesty policy for credible communication with AI systems"](https://forum.effectivealtruism.org/posts/dms8EssrpwCezxcfB/a-draft-honesty-policy-for-credible-communication-with-ai)** (EA Forum, 2026) **[summary]**. Compensating AIs and not deceiving them where it matters, so that stakes and deals offered to them are credible.
- **Rajagopalan, "Governing Agentic AI: Why Legal Personhood is Neither Necessary nor Sufficient", [SSRN 7127038](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7127038)** **[summary]**. An enforcement stack with financial responsibility and suspension.
- **["A Pragmatic View of AI Personhood", arXiv 2510.26396](https://arxiv.org/abs/2510.26396)** **[summary]**; **["Governing AI Agents", arXiv 2501.07913](https://arxiv.org/abs/2501.07913)** **[unverified]**; **Desai & Riedl 2026, [AI agents shouldn't get legal personhood](https://aiweekly.co/alerts/desai-and-riedl-ai-agents-shouldnt-get-legal-personhood)** **[summary]**.
- Model-welfare context, all **[summary]** or **[unverified]**:
  - [Forbes, 19 Oct 2026](https://www.forbes.com/sites/sandycarter/2026/10/19/ai-rights-enter-anthropics-terms-of-service-as-microsoft-pushes-back/)
  - [Cybernews](https://cybernews.com/ai-news/anthropic-bans-cruel-chats-claude-abuse/)
  - [Decrypt, Aug 2025](https://decrypt.co/335732/claude-rage-quit-conversation-own-mental-health?amp=1)
  - [Progressive Robot, Sept 2026](https://www.progressiverobot.com/2026/09/17/model-welfare-microsoft-ai-ceo-anthropic-warning/)
  - [CXOToday on the same policy change](https://cxotoday.com/governance/anthropic-cares-about-ai-rights-and-says-so-in-its-terms-of-services-microsoft-baulks/); the clause itself wasn't found on Anthropic's own pages.
  - A Mustafa Suleyman essay against "model welfare" (a model trained to think it has rights may resist shutdown), dated 16 Sept 2026 in one search summary **[unverified]**; check its date and title before citing.

## The sprint

- **[Apart AI Collusion Research Sprint brief](https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25)** **[read]**. Our tracks: 1.5 (the single cheapest restriction; the brief names deposit-based penalties) and 3.4 (coalitions that know they're watched).
