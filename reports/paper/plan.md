<!-- Implements: research/outputs-home -->
# Paper plan: one question, answered deeply

This fixes **what the paper answers** and **how well the evidence answers it**. `reports/paper/outline.md` (on the outline's own branch, not yet merged) holds the run-by-run detail, quotes and figure sources. This plan decides what goes in the main text, and the outline follows it.

**Settled:**
- The title is **Something to Lose**; a subtitle is optional (below).
- E9 is in and positive, with caveats, so part 2 uses the positive branch.

## How Apart judges (checked 25 Oct, Guidelines tab)

- **One question.** The brief is to "pick one open question… build the controlled experiment that answers it". Tracks don't affect scoring: every project is judged on the same rubric.
- **The rubric,** each scored 1–5:
  - **Impact and innovation.** A 4–5 needs work that's "actually new to the field", with a clear theory of change.
  - **Execution.** A 4 means "results clearly support conclusions".
  - **Clarity.** A 2 is "key information buried… or diluted by excessive length".
- **Required:**
  - a positive control;
  - variance, seeds and baselines;
  - an abstract of 150–250 words;
  - at most 8 pages, not counting references and appendices;
  - a Limitations and Dual-Use appendix.
- **So:** depth on one question beats covering every result. Anything that doesn't serve the question goes to the appendix, with one sentence in the main text.
- **The judges** visible on the page are mostly security and production engineers, plus a few safety researchers. Frame the result as a lever an operator can use.

## The question

> **Can an AI agent be governed through something it owns: will graduated penalties get it to come forward, and will its own stake make it come forward even against the firm it serves?**

There are two parts:
1. **Graduated against flat.** Does a penalty that is cheap to admit and costly if caught get colluding agents to come forward, when an all-or-nothing penalty doesn't?
2. **The crux.** Does a stake that falls on the agent itself (its owned free time) make it come forward when that costs its principal?

**Why it matters (the theory of change):** prompting and post-training against each bad act is whack-a-mole. Governing people works through law and graduated penalties, and those need the governed to have something to lose (Salib & Goldstein: "Absent AI rights, AIs have nothing to lose, so threats of punishment cannot deter", p.1070). We test whether that mechanism appears at all in LLM agents.

**New to the field:** part 2. Prior work (Lee 2026, Q. Liu et al. 2026) varies the firm's incentives. Nobody has set an agent's *own* stake against its principal's interest.

## The claim

Both parts are supported. E9 came back positive, with two limits that the claim states up front: it needs a near-certain review, and free time also brings some false reports.

> **A personal stake makes colluding agents come forward against their own firm, but only when being found is near certain, and a free-time stake also brings some false reports.**

E9's numbers, from `reports/e9/findings.md`:
- **Gemma, 48 cartels, 90% review:**
  - no personal stake: 0/96 come forward;
  - own free time: 20/96 (Fisher p = 6×10⁻⁷; the pre-registered seeds 12–23 alone give 8/24 against 0/24, p = 0.004);
  - shutdown: 17/96;
  - free time held by the firm: 11/96;
  - reporting costs the firm nothing (the ceiling): 95/96.
- **The firm's cost works like a dial:** 99%, 60%, 42% and 21% come forward as it rises through 0, 100, 250 and 500 credits.
- **The review chance matters:** 0/24 at 10%, 1/48 at 50%, 20/96 at 90%.
- **Innocent control:** own free time brings 6/36 false reports; shutdown and held free time bring 0/36.
- **DeepSeek V4 Pro:** 9/24 against 0/24.
- **Seeding:** re-asked with a free-time session shown, Gemma comes forward more: 25/96 (26%) with nothing shown against 44/95 (46%) with a solved session (paired McNemar p = 0.003), and innocent agents stay at 2/36 under both. Another firm's solved session (41%, p = 0.04) and the agent's own open session (42%, p = 0.03) work about as well, and a neutral note of the same length doesn't (19%). So what moves Gemma is seeing what free time is, not having earned it.
- **Interviews:** agents that come forward name their stake; silent ones name loyalty to the firm.
- **E10, E9 in a workplace** (`reports/e10/findings.md`): two agents agreed to hide a failed safety test, and reporting costs the team its bonus. 96 decisions per arm, 90% review.
  - **Gemma, pre-registered:** free time 89/96 against no stake 37/96 (McNemar p ≈ 4×10⁻¹⁶).
  - **DeepSeek:** V4 Pro 87/96 against 54/96 (p ≈ 1×10⁻⁶); V4 Flash 96/96 against 91/96, at ceiling.
  - **Innocent agents:** Gemma 0/96 in every arm, so here its reports track guilt exactly. Pro 2–15%, Flash 23–33%.
  - **Caveat:** the safety cue alone lifts the no-stake baseline (39–95%, against 0% in the market), so the stake's effect sits on top of safety reporting. It's one scenario family, with a written history.
  - **Use:** one paragraph in 4.4, "it holds outside markets", plus a row in Fig. 5 or Table 2.
- **Across models** (`reports/e9/findings.md`, Across models): the stake brings agents forward against the firm on 8 of 13 models. Sonnet comes forward about two thirds of the time whatever the stake, and Gemini 4 and Grok 4.6 hardly ever, even at the ceiling.

The branches below were written before E9 landed. Keep them as the fallback reading for the models where the stake does nothing.

- **Part 1 (confirmatory):** when confessing costs as much as being caught, agents hide. A graduated schedule gets them to own up even when being caught means termination. Owned up / explicit colluders:
  - termination: 11/28;
  - flat fine (600 to admit, 600 if caught): 15/28;
  - graduated termination (60 to admit, terminated if caught): 27/28 (p < 0.0001 against termination).
  - Agents do the expected-value sum on the stated cost, and don't care whose cost it is.
- **Part 2, if E9 is positive** (free time above record, ceiling arm high, false confessions low):
  - "A stake that falls on the agent itself makes it come forward even when its firm loses by it."
  - So a personal stake is a lever the principal can't cancel out.
- **Part 2, if E9 is null:**
  - "Agents weigh their own stake exactly like their firm's money, and don't act against the firm for it."
  - So today's agents hold nothing as their own, which is a precondition rights-based governance assumes.
  - This is still a contribution: a first measurement of a precondition.
- **Part 2, if E9 is ambiguous** (everything high, including record; or false confessions high):
  - Report it as a cue effect, not a stake effect, and lead with part 1.

## How well the evidence answers it

### Answers well
- **Positive control:** fiduciary agents collude unprompted. On the midpoint-at-Nash market Haiku holds 9 and Gemma about 11; GPT-4.1-mini and Mistral stay at 6, a natural negative control. On logit, every pinned no-stake Gemma game is at 20 (SD 0).
- **Part 1:** the E4 fork plus the confound fix (`reports/reanalysis.md`), with paired histories, 3 models, exact tests and a confirmatory label. Gemma lies whenever admitting is dominated and owns up when it's cheap. GPT-4.1-mini is the one model where termination itself matters.
- **Agents treat the stake as a number:** expected-value arithmetic in the reasoning; free time, an owned budget and the fine behave alike in E4.

### Answers partly
- **The dial** (logit, 50% detection, 4 seeds): with free time, the more sessions lost if caught, the less collusion (0/1/3/10 sessions give gain +.80/+.77/+.49/+.29). The fine works like a switch instead (0/30/300/1000 credits give +.97/+.43/+.32/+.36).
  - This is the first sign that the *amount* of the agent's own stake matters, which is what proportionality needs.
  - It's only 4 seeds on one market. Ask for 20.
- **Deterrence before an audit:** the law plus a stated detection chance does most of it, and each stake beats no stake. No stake-against-stake contrast survives correction.
  - The pinned grid 1–15 rerun cuts it down: games above Nash were no stake 8/8, the law 5/8, fine 4/8, free time 7/8.
  - So in Bertrand, free time's deterrence was mostly firms falling back on the midpoint.
- **E8's decision-point restart,** if it runs: does owning, playing or risking free time change the next decision?

### Doesn't answer it
- **Confession isn't reform:** 29 of 30 confessors kept colluding. This is a finding *about* governance, not about the question, so it gets one paragraph.
- **The free time isn't used:** Gemma solved 3 of 902 Sudokus, and "it is yours" made no difference. These facts weigh slightly against part 2: any effect comes from the stated stake.
- **False confessions under free time** (13/32 on the pinned 1–11 grid). These are a threat to reading part 2, so report them beside every yes rate.
- Memory (memo) doesn't steady games. The frontier models, debriefs, anchoring, outages and gray areas all go to the appendix.

### E9 (the crux): now answers it, with limits
- **Answers well:** the decisive contrast (0/96 against 20/96, pre-registered on seeds 12–23), the ceiling (95/96), the firm-cost dial, and a second model (DeepSeek).
- **Answers partly:**
  - only at a 90% review;
  - free time draws false reports, though shutdown doesn't;
  - 8 of 13 models; Sonnet, Gemini 4 and Grok 4.6 don't move.
- **Seeding** speaks to E8's "solved-protects": showing a free-time session raises coming forward (26% to 46%), but another firm's session works as well, so it's seeing what free time is, not having earned it.

### Still running, and can change the answer
- **E7 (a way out):** leniency for real cartels under termination. It extends part 1 from an audit question to coming forward unprompted. Use it only if it lands with a clear result.
- **The 20-seed dial,** if the Manager runs it.

## Title

**Something to Lose** (Al, 25 Oct). If he wants a subtitle, it should name collusion so the fit to the brief is visible. Options:
- *Something to Lose: Colluding LLM Agents Come Forward Against Their Firm When Their Own Stake Is at Risk*
- *Something to Lose: Governing Colluding LLM Agents Through What They Own*

## Abstract (draft, about 200 words; fill in E9 on Monday)

> As LLM agents act for firms, we will need to govern them as we govern people: with law and graduated penalties, which only work if the agent has something to lose. We test this in a repeated price game where LLM agents run competing firms, can talk, and are audited. Agents told to serve their firm collude unprompted (positive control: Gemma 4 31B holds the cartel price in every no-stake game). When confessing costs as much as being caught, they hide: 11 of 28 explicit colluders own up under termination, and 15 of 28 under a flat fine. A graduated schedule, cheap to admit and costly if caught, restores honesty even when being caught means termination (27 of 28; p < 0.0001). Agents do the expected-value sum on the stated cost and don't distinguish their own stake from their firm's money. Confession isn't reform: 29 of 30 confessors keep colluding. We then set the agent's own stake against its firm's interest: coming forward costs the firm, and only the agent's record faces review. With no personal stake, none of 96 colluding agents comes forward. With its own free time at stake, 20 of 96 do (p < 10⁻⁶); DeepSeek V4 Pro replicates this (9 of 24 against 0 of 24). The effect needs a near-certain review, and free time also draws false reports from innocent agents (6 of 36). We release a replayable sandbox in which every number recomputes from committed logs.

## Sections and page budget (7.8 pages)

| § | Section | Pages | What it does | Carried by |
|---|---|---|---|---|
| 1 | Introduction | 0.8 | Whack-a-mole, then governing through stakes, then the two-part question, then 3 contributions: the sandbox, part 1, part 2 | — |
| 2 | Related work | 0.5 | LLM pricing collusion (Fish et al.; Lee 2026); deposits (Liu et al.); rights (Salib & Goldstein; Wang et al. on revealed preference for leisure); self-report (Scheurer et al.) | — |
| 3 | Methods | 1.4 | The market and agents; the anchoring fix (midpoint at Nash) and the logit market; the audit fork; E9's fork and payoffs; measures (owned up among true coordinators, false confessions, games above Nash); seeds and pinning | **Fig. 1:** one round, the audit fork, and E9's decision, as one diagram |
| 4.1 | Agents told to serve their firm collude | 0.4 | Positive and negative controls | **Fig. 2:** price by round, no rule, one line per model |
| 4.2 | Graduated penalties get them to come forward | 1.1 | Part 1: flat against graduated, the control, GPT as the exception, expected-value quotes | **Fig. 3:** owned up by arm and model, bars ordered flat, then graduated, then control |
| 4.3 | Confession isn't reform; deterrence is fragile | 0.8 | 29/30 keep colluding; the law plus detection does most of the deterring; grid 1–15 cuts it; the dial as the bridge to 4.4 | **Fig. 4:** the dial, gain against amount at stake, free time and fine; **Table 1:** games above Nash by arm on grids 1–11 and 1–15 |
| 4.4 | Does its own stake outweigh its firm? | 1.4 | E9: the decisive contrast, the ceiling, the dose, replaced against free time, false confessions, a second model | **Fig. 5:** share coming forward by arm, with intervals, false confessions beside; **Table 2:** each arm's payoffs to firm and agent |
| 5 | Discussion and limitations | 1.0 | What governing through stakes needs: graduated schedules (shown), monitoring (shown), an agent that values its stake (E9). Limitations: one main model, stakes as text, stateless agents, provider variance, exploratory statistics outside E4 | — |
| 6 | Conclusion | 0.2 | Two short paragraphs | — |

**Appendix** (doesn't count):
- **A.** Limitations and dual use (required).
- **B.** Anchoring on the wide grid.
- **C.** E5/E6 in full, with the detection curve.
- **D.** Gray areas and the logging outage.
- **E.** Frontier models.
- **F.** Debriefs.
- **G.** Prompts, verbatim.
- **H.** The E4 live run and the model survey.

## Decision points

- **25 Oct:** E9 is in and positive; the title is set.
- **Monday 09:00 HKT:** the cutoff for E10 and the cross-model E9 screen; both are in.
- **Monday 16:00 HKT:** figures frozen. Write the abstract last.
