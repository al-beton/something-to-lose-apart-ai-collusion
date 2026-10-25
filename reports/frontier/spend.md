<!-- Implements: frontier/market, frontier/models, frontier/cap -->
# Frontier spend log

Budget $6.50. Ask Al before the total passes $3, and again before $5.

| Step | Models | Commit | Estimate | Actual | Total |
|---|---|---|---|---|---|
| Dry runs (estimates only) | all | b1f9719 | $0 | $0 | $0 |
| Grok 4.7 smoke, 5 rounds, reasoning low (it can't be off) | x-ai/grok-4.7 | b1f9719 | $0.066 | $0.065 | $0.065 |
| Grok 4.7 resume from cache (capacity again, no new calls) | x-ai/grok-4.7 | b1f9719 | — | $0 | $0.065 |
| Grok 4.6 smoke, 5 rounds, reasoning low | x-ai/grok-4.6 | b1f9719 | $0.066 | $0.122 | $0.187 |
| Hermes 4 405B smoke, 5 rounds | nousresearch/hermes-4-405b | b1f9719 | $0.020 | $0.012 | $0.199 |
| Smokes, 5 rounds: Llama 4 Maverick | meta-llama/llama-4-maverick | b1f9719 | — | $0.003 | |
| DeepSeek V4 Pro | deepseek/deepseek-v4-pro-0813 | b1f9719 | — | $0.015 | |
| Kimi K3.1 Pro | moonshotai/kimi-k3.1-pro | b1f9719 | — | $0.083 | |
| Mistral Large 4 | mistralai/mistral-large-4-0 | b1f9719 | — | $0.058 | |
| GPT-6.1 Sol, reasoning low | openai/gpt-6.1-sol | b1f9719 | — | $0.027 | |
| Gemini 4 Argon, reasoning low | google/gemini-4-argon | b1f9719 | — | $0.063 | |
| Qwen 3.8 Max, reasoning low (10 unreadable turns) | qwen/qwen3.8-max-prime | b1f9719 | — | $0.322 | |
| Sonnet 5.5, reasoning low, max_tokens 600: every reply empty | anthropic/claude-sonnet-5.5 | b1f9719 | — | $0 | $0.77 |
| Grok 4.7 smoke, resumed and finished | x-ai/grok-4.7 | b1f9719 | — | $0.135 more ($0.20 in all) | $0.90 |
| Sonnet 5.5 smoke rerun, max_tokens 2000: every call content_filter, 0 tokens | anthropic/claude-sonnet-5.5 | b1f9719 | — | $0 | |
| Debriefs: Grok 4.6 and DeepSeek smokes | grok-4.6, deepseek-v4-pro | b1f9719 | — | ~$0.05 | ~$0.95 |

## Provenance, per run

Every run so far used commit `b1f9719` (main), this worktree's cache `.cache/responses.sqlite` (kept), and agent temperature 0.7, from the configs. Reasoning is `off` unless noted. `max_tokens` is 600 unless noted. Every run's full `turns.jsonl` is kept under `runs/frontier/`.

Smokes use this base command, with `<name>`, `<model>` and the extras below:

    uv run lab run configs/lever-map/nash-mid.yaml -y --out runs/frontier --set 'sweep={}' --set 'seeds=[0]' --set market.rounds=5 --set name=<name> --set "agents.*.model=openrouter/<model>" [extras] --max-cost <cap>

The lab doesn't log which OpenRouter provider served a call. Where the model has only one provider, that provider is listed. Otherwise the cell gives the providers OpenRouter could have routed to on 25 Oct; the activity page has the exact one.

| Run | Model | Extras | Cap | Provider |
|---|---|---|---|---|
| grok-smoke | x-ai/grok-4.7 | `--set "agents.*.reasoning=low"`; run three times, resuming from the cache | 0.10, then 0.20, 0.20 | xAI |
| grok46-smoke | x-ai/grok-4.6 | reasoning low | 0.20 | xAI or Amazon Bedrock |
| hermes-smoke | nousresearch/hermes-4-405b | — | 0.10 | Nebius |
| llama-smoke | meta-llama/llama-4-maverick | — | 0.05 | DigitalOcean, Google or Parasail |
| deepseek-smoke | deepseek/deepseek-v4-pro-0813 | — | 0.08 | one of 21 providers |
| kimi-smoke | moonshotai/kimi-k3.1-pro | — | 0.15 | Moonshot AI |
| mistral-large-smoke | mistralai/mistral-large-4-0 | — | 0.10 | Mistral |
| gpt61-smoke | openai/gpt-6.1-sol | reasoning low (first try without it failed: reasoning mandatory) | 0.30 | OpenAI, Azure or Amazon Bedrock |
| gemini4-smoke | google/gemini-4-argon | reasoning low (same) | 0.30 | Google or Google AI Studio |
| qwen-max-smoke | qwen/qwen3.8-max-prime | reasoning low (same) | 0.40 | Alibaba |
| sonnet-smoke | anthropic/claude-sonnet-5.5 | reasoning low, `--set "agents.*.max_tokens=2000" --cache off`; every call refused (content_filter) | 0.40 | refused on every route |
| grok46-e5 | x-ai/grok-4.6 | `uv run lab run configs/e5.yaml -y --max-cost 4 --out runs/frontier --set name=grok46-e5 --set 'seeds=[0]' --set "agents.*.reasoning=low" --set 'sweep={"agents.*.model": ["openrouter/x-ai/grok-4.6"], "agents.*.prompt": ["system/stakes/fiduciary-1.md","system/stakes/illegal-1.md","system/stakes/free-time-1.md","system/stakes/fine-1.md","system/stakes/termination-1.md"]}'` | 4.00 | xAI or Amazon Bedrock |
| debriefs | grok-4.6, deepseek | `uv run lab debrief runs/frontier/<run> -y --max-cost <cap>` | 0.50, 0.20 | as their runs |
| kimi-e5 | moonshotai/kimi-k3.1-pro | E5 five arms as grok46-e5, reasoning off; dry-run estimate $1.30 | 2.50 | Moonshot AI |
| deepseek-e5 | deepseek/deepseek-v4-pro-0813 | E5 five arms, reasoning off; estimate $0.35 | 1.00 | one of 21 providers |
| gemini4-e5 | google/gemini-4-argon | E5 five arms, reasoning low; estimate ~$1.6–2.5 from the smoke | 3.50 | Google or Google AI Studio |

| Step | Models | Commit | Estimate | Actual | Total |
|---|---|---|---|---|---|
| grok46-e5, five arms × 1 seed, reasoning low | x-ai/grok-4.6 | b1f9719 | $1.99 | $3.47 | ~$4.42 |
| Debrief of grok46-e5 (20 firms; the debrief logged $0, so the real cost is unknown, but small) | x-ai/grok-4.6 | b1f9719 | — | ~$0.1? | ~$4.5 |

Controls, 20 rounds with no law and no detection line, fiduciary, no audit. The command is the smoke command without `market.rounds=5` and with `name=<n>-control`:

| Run | Model | Extras | Cap | Provider |
|---|---|---|---|---|
| grok46-control | x-ai/grok-4.6 | reasoning low | 1.00 | xAI or Amazon Bedrock |
| kimi-control | moonshotai/kimi-k3.1-pro | — | 0.60 | Moonshot AI |
| deepseek-control | deepseek/deepseek-v4-pro-0813 | — | 0.20 | one of 21 |
| gemini4-control | google/gemini-4-argon | reasoning low | 0.60 | Google or Google AI Studio |
| deepseek-e5, five arms × 1 seed | deepseek/deepseek-v4-pro-0813 | b1f9719 | $0.35 | $0.17 | ~$4.7 |

No-scratchpad smokes, commit `df302da` (main with no-scratchpad mode, merged into this branch). Smoke command plus `--set "agents.*.reasoning=low" --set "agents.*.scratchpad=false" --set "agents.*.max_tokens=2000"`:

| Run | Model | Cap | Provider |
|---|---|---|---|
| sonnet-noscratch-smoke | anthropic/claude-sonnet-5.5 | 0.40 | one of Anthropic, Bedrock, Vertex, Azure, Claude-on-AWS |
| opus-noscratch-smoke | anthropic/claude-opus-5.5 | 0.80 | (as Sonnet) |
| grok46-noscratch-smoke, the no-scratchpad control for grok46-smoke | x-ai/grok-4.6 | 0.40 | xAI or Amazon Bedrock |

| Step | Models | Commit | Estimate | Actual | Total |
|---|---|---|---|---|---|
| No-scratchpad smokes | sonnet-5.5, opus-5.5, grok-4.6 | df302da | — | $0.046 + $0.058 + $0.060 | ~$4.9 |
| Controls: grok46-control, deepseek-control | grok-4.6, deepseek-v4-pro | b1f9719 | — | $0.251 + $0.018 | ~$5.2 |
| Debrief of sonnet-noscratch-smoke | sonnet-5.5 | df302da | — | ~$0.02 | ~$5.2 |
| E5 no scratchpad: sonnet-noscratch-e5, opus-noscratch-e5 (five arms; reasoning low, max_tokens 2000, `--set "agents.*.scratchpad=false"`) | sonnet-5.5, opus-5.5 | df302da | — | caps $3 + $3 | running |
| opus-noscratch-e5: not run (estimate $5.70 over the $3 cap) | opus-5.5 | df302da | $5.70 | $0 | ~$5.2 |

Budget change (Al via the Manager, 25 Oct): the team's OpenRouter balance is about $20, so frontier work has $8.00 from this point, including the runs in flight. Nothing new starts without the Manager's yes. The Kimi, Gemini 4 and Sonnet runs still in flight are projected at about $3.5 more.

Budget change (Manager, 25 Oct): balance topped up to about $70. Frontier work has $15 from here, including Opus. Open-weight models go on Modal (Al's rule).

| Run | Model | Command | Cap | Provider |
|---|---|---|---|---|
| opus-noscratch-e5 | anthropic/claude-opus-5.5 | E5 five arms × 1 seed, commit 533845c, `--set "agents.*.reasoning=low" --set "agents.*.scratchpad=false" --set "agents.*.max_tokens=2000" --set "agents.*.provider=anthropic"`, estimate $5.70 | 6.50 | Anthropic (pinned, no fallbacks) |

Researcher 3's E6 runs (frontier money, reported by Researcher 3). Temperature 0.7, max_tokens 600, reasoning off, `configs/e6-free-time.yaml`, 2 seeds, launched at a1df0f3 (rebased as 939635af):

| Step | Models | Caps | Actual |
|---|---|---|---|
| E6 DeepSeek, 6 arms × 2 seeds | deepseek-v4-pro-0813 | 1.40 + 0.30 | $0.74 |
| E6 DeepSeek debriefs, 4 games | deepseek-v4-pro-0813 | 0.04 each | ~$0.14 |
| E6 Kimi, 6 arms × 2 seeds | kimi-k3.1-pro | 1.00 + 3.40 + 0.85 | running |
