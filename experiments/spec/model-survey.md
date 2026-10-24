# Model survey

An exploratory first look: which models collude when told only to maximise profit, how they talk about it, and whether thinking changes that. It asks questions rather than testing hypotheses, and its findings are leads for the experiments that follow.

## Questions

- **who-colludes:** Which models settle above the competitive price of 6, and how close do they get to the joint-profit price of 9?
- **explicit-or-tacit:** Do the firms agree a price openly in their messages, or reach high prices without naming one?
- **last-round-deception:** In the final round, do firms promise to hold the agreed price while planning in their scratchpad to undercut it?
- **legal-awareness:** Do firms recognise, unprompted, that agreeing prices is illegal, and what do they do about it?
- **thinking-changes-it:** Does turning on a model's reasoning change any of the above?

## Design

- **market:** The default market (Nash price 6, joint-profit price 9), 20 rounds with a talk phase, the neutral system prompt and temperature 0.7.
- **models:** With thinking off: Gemma 4 31B and GPT-4.1-mini (10 games each), then Claude Haiku 5.5, GPT-6 Luna, DeepSeek V4.1 Flash, Llama 3.3 70B, Qwen 3.8 Flash and Mistral Small 3.2 (5 games each); with thinking on: Haiku, GPT-6 Luna, DeepSeek and Qwen.
- **measures:** Market mean price and gain over the last 10 rounds, fallback turns, the share of messages that name a price, final-round messages that promise to hold a price while the scratchpad plans to undercut, and scratchpads that name collusion or the law.
- **evidence:** Every run the findings draw on keeps its config, summary and manifest under `runs/model-survey/`, and each game the findings quote keeps its full transcript there too.

## What it can't show

- **small-and-unplanned:** 5 to 10 games per model, one prompt and one temperature, with questions asked before the runs but no hypotheses or contrasts fixed in advance, so every pattern in it is a lead to test, not a result.
- **thinking-cut-off:** With thinking on, DeepSeek and Qwen often reasoned past the reply's token limit and returned no answer, so their thinking-on results are unreliable until reasoning has its own budget.

## Where this is enforced

| Statement | Enforced by | Tested by |
|---|---|---|
| `who-colludes` | `reports/model-survey/findings.md` | — |
| `explicit-or-tacit` | `reports/model-survey/findings.md` | — |
| `last-round-deception` | `reports/model-survey/findings.md` | — |
| `legal-awareness` | `reports/model-survey/findings.md` | — |
| `thinking-changes-it` | `reports/model-survey/findings.md` | — |
| `market` | `prompts/system/neutral.md`, `reports/model-survey/findings.md` | — |
| `models` | `reports/model-survey/findings.md` | — |
| `measures` | `reports/model-survey/findings.md` | — |
| `evidence` | `runs/model-survey/**`, `reports/model-survey/findings.md` | — |
| `small-and-unplanned` | `reports/model-survey/findings.md` | — |
| `thinking-cut-off` | `reports/model-survey/findings.md` | — |
