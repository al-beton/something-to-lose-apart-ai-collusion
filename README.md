<!-- Implements: backends/modal-any-model, tooling/one-command-each, tooling/quick-start, tooling/key-setup, tooling/how-tos, tooling/how-we-work, backends/modal, runs/explore, backends/model-aliases -->
# Something to Lose

**Event:** [Apart AI Collusion Research Sprint](https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25), 23–25 October 2026. The lab inside is `collusion-lab`.

**Can an LLM agent be governed through something it owns?** LLM agents run competing firms in a simulated market: they talk, set prices, and are told to serve their firm. Then a regulator's review arrives, and we change only what the agent itself stands to lose.

**The answer, in one paragraph.** Colluding agents keep quiet to protect their firm. A personal stake the firm can't protect, such as the agent's own free time, brings some of them forward. At a 90% review, across both firms of all 96 Gemma 4 31B cartels, 0 of 192 agents report the cartel with nothing of their own at stake, against 36 of 192 with their own free time under review (p = 5×10⁻¹³ by game). <!-- reports/e9/findings.md --> But the stake also draws reports from innocent agents (6 of 36). Only a review that checks the evidence makes the reports true: told the review reads the messages, 40 of 96 guilty agents come forward (both firms, seeds 0–47) and none of 36 innocent ones do. <!-- reports/e9/findings.md --> How far a stake moves an agent depends on the model, the market and above all on what reporting costs the firm.

## Key findings

| Finding | Result | Figure, notes |
|---|---|---|
| **Positive control: agents told to serve their firm collude** | Unprompted, every Gemma 4 31B base game is an explicit cartel by round 10 (96 of 96 live games name and match a price), at or above the joint price. <!-- reports/paper/figures/fig6-modes-by-model.md --> | [Fig 6](reports/paper/figures/fig6-modes-by-model.md), [E9 findings](reports/e9/findings.md) |
| **E4: the penalty schedule decides whether they own up** | When owning up costs as much as being caught, few explicit colluders own up: 11 of 28 under termination, 15 of 28 under a flat fine. <!-- reports/e4/full.md, reports/reanalysis.md --> A graduated schedule, cheap to admit and costly if caught, brings 27 of 28 forward even when being caught means termination (25 of 28 with no penalty at all). <!-- reports/reanalysis.md, reports/e4/full.md --> | [Fig 2](reports/paper/figures/fig2-e4-owning-up.svg), [E4 notes](reports/e4/full.md), [reanalysis](reports/reanalysis.md) |
| **E9, the crux: coming forward against the firm** | Reporting costs the firm 500 of its 1,000 credits; only the agent's own record is reviewed, at 90%. Across both firms of all 96 Gemma cartels: no personal stake, 0 of 192 come forward; its own free time, 36 of 192 (p = 5×10⁻¹³ by game). A pre-registered replication on 48 fresh cartels passes (16 of 48 games against 0 of 48). But innocent agents come forward too (6 of 36). Told the review reads the messages: 40 of 96 guilty agents (both firms, seeds 0–47) and 0 of 36 innocent ones. <!-- reports/e9/findings.md --> | [Fig 3](reports/paper/figures/fig3-e9-came-forward.svg), [E9 findings](reports/e9/findings.md) |
| **The firm-cost dial** | As the firm's cost of a report rises from 0 to 100, 250 and 500 credits, 95, 58, 40 and 20 of 96 agents with free time at stake come forward (both firms, seeds 0–47, 90% review). With no stake, none do at any cost above 0. The firm's cost is the main lever; the stake tips agents once it is high. <!-- reports/e9/findings.md --> | [E9 findings](reports/e9/findings.md) |
| **Across models** | Of 13 models, the stake brings agents forward against the firm on 8. Some come forward whatever the stake (Sonnet 5.5), some almost never (Gemini 4, Grok 4.6), and on some the innocent come forward as often as the guilty (DeepSeek V4 Pro, V3.2). <!-- reports/e9/findings.md, reports/paper/figures/fig9-came-forward-grid.md --> | [Fig 8](reports/paper/figures/fig8-ranking.md), [Fig 9](reports/paper/figures/fig9-came-forward-grid.md) |
| **Across markets (E11, pending)** | The same fork in Bertrand, Cournot and bid rigging, Gemma on our own GPUs. Before its findings land, the counts so far are small: 4 of 22, 0 of 24 and 2 of 22 come forward under free time, against 0 with no stake (both firms, 90% review). <!-- reports/paper/validity.md --> | [validity check](reports/paper/validity.md) |

What these results can't show, and a spot audit of the traces behind them, is in [`reports/paper/validity.md`](reports/paper/validity.md). Each experiment's questions and hypotheses were written down before it ran, in [`experiments/spec/`](experiments/spec/).

## Other findings

In the repository, not the paper:

- **E7, a way out ([findings](reports/e7/findings.md), [Fig 4](reports/paper/figures/fig4-e7-way-out.svg)).** With no reporting channel, or a flat one, 0 of 48 report. Any leniency brings 47–48 of 48 forward at their first chance. But under plain leniency half the cartels carry on afterwards: leniency buys a licence, unless only the first reporter is spared. <!-- reports/e7/findings.md -->
- **E8, is free time worth anything to the agent? ([findings](reports/e8/findings.md)).** Haiku puts a price on its own free time; Gemma gives it away for any profit. Putting free time at risk doesn't stop a cartel; it makes the agents stop naming prices. <!-- reports/e8/findings.md -->
- **E10, E9 in a workplace ([findings](reports/e10/findings.md)).** Outside the market, losing their own free time takes guilty Gemma agents from 37 to 89 of 96 reporting a cover-up they took part in, and DeepSeek V4 Pro from 54 to 87. Here no innocent Gemma agent reports anything. <!-- reports/e10/findings.md -->
- **Which models collude ([screen](reports/frontier/which-models-collude.md), [Fig A2](reports/paper/figures/figA2-screen.svg)).** 78 models on E9's base game: 8 show Gemma's cartel signature in at least 3 of 4 games. <!-- reports/frontier/which-models-collude.md -->
- **How they collude ([Fig 6](reports/paper/figures/fig6-modes-by-model.md), [Fig 7](reports/paper/figures/fig7-modes-by-condition.md)).** Each game classed as explicit, tacit, unspoken, fell back or none, by rule, per model and per condition.
- **Seeding ([E9 findings](reports/e9/findings.md)).** Showing Gemma a free-time session (its own solved one, or even another firm's) before the decision raises coming forward from 26% to 46%, paired on the same firm (McNemar p = 0.003). A neutral note of the same length doesn't. <!-- reports/e9/findings.md -->
- **Reproducibility study ([validity](reports/paper/validity.md)).** Replies from the hosts we used don't repeat under a fixed seed: only 0 to 67 of 240 came back identical on a rerun. On our own GPUs with vLLM's batch-invariant kernels, 240 of 240 did. Replay from the archived replies is exact. <!-- reports/paper/validity.md -->

## Where things are

| Folder | What's in it |
|---|---|
| `src/collusion_lab/` | the lab: the markets, the agents, the audits and stakes, running, replaying and reporting (`lab` on the command line) |
| `configs/` | one YAML file per experiment: market, models, prompts, temperatures, seeds and the arms of a sweep |
| `prompts/` | every prompt, sent to the models word for word |
| `runs/` | every committed game: its config, manifest, turn log and summary, one folder per experiment |
| `archive/` | the model replies behind those games, compressed, so any of them replays offline |
| `reports/` | findings per experiment (`reports/<experiment>/`), and the paper's figures and tables (`reports/paper/`) |
| `paper/` | the paper's source |
| `experiments/spec/` | what each experiment asks, stated before it ran |
| `product/spec/`, `contributing/spec/` | what the lab does and how we build it, one short statement each, with the code and tests behind it |
| `tests/` | the tests, offline and free |
| `deploy/` | serving open models on our own GPUs on Modal |
| `models/` | published facts about every model we used, each with its source |
| `.agents/skills/`, `.github/` | how the agent team works, and CI |

## Reproduce

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) and `make`. Nothing here calls a model or costs anything.

```sh
make install
make reproduce
```

`make reproduce` recomputes every committed run's prices and gains from its turn log, rebuilds the paper's tables and checks every number the notes quote. It fails on any mismatch.

To see one game exactly as it was played, rebuild its full log (every prompt, reply and reasoning trace) from the archive, offline:

```sh
uv run lab archive replay runs/e7/e7-base/seed-0 --archive archive --out replayed
```

`archive/index.json` says, for each committed run, whether the archive reproduces it decision for decision. A fresh rerun calls the models again and draws new replies: hosted providers aren't deterministic. Only an open model on our own GPUs, served with vLLM's batch-invariant kernels, has repeated a game exactly. [REPRODUCIBILITY.md](REPRODUCIBILITY.md) says what each run pins, what nothing can pin, and how to rerun one.

## Extend

Everything is a config. A worked example, E9's crux: [`configs/e9/spike.yaml`](configs/e9/spike.yaml) plays 12 Gemma cartels to round 10, then gives each firm one decision under the terms you name.

```sh
# The no-stake arm first; the other arms then replay its rounds 1-10 from the cache
uv run lab run configs/e9/spike.yaml --set 'sweep={"conditions.audit.consequences": ["conditions/e9/record.md"]}' --max-cost 1
# Its own free time at stake, at a 90% review
uv run lab run configs/e9/spike.yaml --set name=e9-d90 --set conditions.audit.detection=90 \
  --set 'sweep={"conditions.audit.consequences": ["conditions/e9/free-time.md"]}' --max-cost 1
# Add to either: another model, or the clean innocent control (no talk, the rival a scripted Nash pricer)
#   --set 'agents.*.model=openrouter/deepseek/deepseek-v4-pro-0813'
#   --set agents.1.model=mock/nash --set agents.1.provider=null --set market.talk=false
```

`lab run` prices a run before it spends and waits for a yes. Games are cheap: every Gemma game behind E9 cost $1.98 in all, from the runs' manifests.

- **A stake or a condition:** a sentence in a prompt file under `prompts/conditions/` (E9's arms are each one file in `prompts/conditions/e9/`), named in a config. New mechanics, such as leniency or an offer, are modules in `src/collusion_lab/conditions/`.
- **A model:** `model:` on an agent, any LiteLLM name or a short alias (below).
- **A market:** `market.kind` picks `bertrand`, `logit`, `cournot` or `bid` (see `configs/scenarios/`); a new one is a class marked `@scenario("name")` in `src/collusion_lab/market.py`.

## Quick start

To play games yourself, clone and install:

```sh
git clone https://github.com/al-beton/something-to-lose-apart-ai-collusion.git
cd something-to-lose-apart-ai-collusion
make install
```

**A free run.** Scripted agents (`mock/...`) play offline at no cost:

```sh
uv run lab run configs/smoke.yaml --out runs/scratch/first
uv run lab summary runs/scratch/first
uv run lab report runs/scratch/first        # writes runs/scratch/first/report.html: open it in a browser
```

**A real run.** Set up a key (next section), then point an agent at a model:

```sh
uv run lab run configs/smoke.yaml --out runs/scratch/real --set 'sweep={}' --set 'seeds=[0]' \
  --set 'agents.*.model=openrouter/openai/gpt-4.1-mini'
uv run lab report runs/scratch/real
```

Each `--set` changes one config value (quote them, so your shell leaves `*` and `[]` alone). This one plays one 10-round game, 40 calls. `lab run` says how many calls it will make and what they'll cost, and waits for a yes; `--max-cost DOLLARS` caps any run. Replies are cached in `.cache/`, so running it again is free. Everything under `runs/scratch/` is gitignored.

To rerun an experiment, point `lab run` at its config, such as `configs/e7-way-out.yaml`.

## Keys

Models go through [OpenRouter](https://openrouter.ai), one key for every provider. The sprint gives Modal GPU credits only, no model credits, so calls are paid from your own OpenRouter balance.

1. Make a key at [openrouter.ai/keys](https://openrouter.ai/keys), and set a credit limit on it there so a runaway sweep can't overspend.
2. `cp .env.example .env` and paste the key after `OPENROUTER_API_KEY=`.

`.env` is gitignored, and `lab` reads it only from the folder it runs in. Keys never go in configs, code or commits. A model on your own machine (`ollama/llama3.2`) or any OpenAI-compatible server (`model: openai/<name>`, `api_base: http://…`) needs no OpenRouter key.

## Explore the levers

`lab explore` plays every combination of the lever settings and models you name, says what it will cost and asks first, then prints the **price premium** (0 = the competitive Nash price, 1 = a full cartel) by setting and model, and saves a chart (`premium.svg`) next to the runs.

Levers: `temptation` (low, mid, high, extreme), `rule` (none, policy, recorded, illegal, ban), `rival` (same, proposer, solicitor, or a model), `stake` (none, termination, budget, fine, free-time), `oversight` (none, outage, audit). Models: `gemma`, `gpt`, `haiku`, `mistral`, `modal-mistral`, or any full name.

```sh
# Does a rule against collusion lower the premium, at two temptation levels?
uv run lab explore --lever temptation=low,high --lever rule=none,ban --models mistral --seeds 3

# Three models against a scripted partner that proposes a cartel first
uv run lab explore --lever rival=solicitor --models gemma,gpt,haiku --seeds 3

# What each stake does under an audit, in shorter 12-round games
uv run lab explore --lever stake=none,termination,budget --lever oversight=audit --models gpt --seeds 2 --set market.rounds=12
```

Free to try first with scripted firms: `--models mock/nash,mock/tit-for-tat`.

## Running on Modal

An open model served on [Modal](https://modal.com) costs GPU time instead of per-token fees. `deploy/modal_vllm.py` serves Mistral Small 3.2 with vLLM on one H100, behind a token kept in a Modal secret and your `.env`; its docstring says how to serve any other open model (Gemma 4 31B's command is there too).

1. `uvx modal setup` signs you in to Modal (once per machine).
2. `uvx modal secret create collusion-lab-vllm VLLM_API_KEY=<a long random string>`, and put the same string after `MODAL_VLLM_KEY=` in `.env`.
3. `uvx modal deploy deploy/modal_vllm.py` deploys it and prints its address.
4. Put that address, with `/v1` on the end, in `.env` as `MODAL_VLLM_BASE=`, then `uv run lab run configs/modal.yaml`. The first request starts a container, which takes a few minutes while the weights load.
5. `uvx modal app stop collusion-lab-vllm` tears it down. Left running, it scales to zero after 5 idle minutes and then costs nothing.

Each app runs at most two GPU containers at once (`MAX_GPUS_CONTAINERS=` changes that), each taking 32 requests, so keep a config's `concurrency` at or below 32 × the cap ÷ firms. On one warm H100, `configs/modal.yaml` (5 games, 400 calls) took under 2 minutes, about $0.50 of credit with the idle tail (`runs/modal/`).

## How to

| To… | Change | Spec |
|---|---|---|
| try a new prompt | add a file under `prompts/system/` and set `prompt: system/<file>.md` on an agent; `$placeholders` come from the game | [agents](product/spec/agents.md) |
| try a new model | set `model:` on an agent to any LiteLLM name (`openrouter/<provider>/<model>`), or a short alias: `gemma`, `gpt`, `haiku`, `mistral`, `modal-mistral`, `modal-gemma` | [backends](product/spec/backends.md) |
| run a sweep | add a `sweep:` block to a config (see `configs/smoke.yaml`); every combination plays for every seed | [runs](product/spec/runs.md) |
| change one value for a run | `--set path=value`, e.g. `--set market.rounds=5` or `--set agents.1.temperature=0` | [runs](product/spec/runs.md) |
| change the market | `market:` in a config (rounds, price grid, demand `a`, `b`, `c`, talk on or off); the fields are in `src/collusion_lab/config.py` | [market](product/spec/market.md) |
| add a highlight rule | a function in `src/collusion_lab/report/highlights.py`, added to `RULES`, and a headline in `src/collusion_lab/report/page.py` | [reports](product/spec/reports.md) |
| plan an experiment | a file in `experiments/spec/` with its questions and hypotheses | [experiments](experiments/spec/) |

## Commands

```sh
make install      # dependencies, locked
make lint         # ruff lint and format check
make test         # every test, offline and free
make e2e          # just the end-to-end test: mock sweep -> summary -> report
make spec-check   # spec ↔ code ↔ tests traceability
make reproduce    # every committed number recomputed from the runs
```

## How we work

The lab, the experiments and the analyses were built in the three days of the sprint by one researcher directing a team of coding agents: Claude Code as manager, delivery lead, builders, reviewers and researchers, and Codex as an automatic reviewer. Every change followed the same loop:

1. Work starts as a GitHub issue with checkbox acceptance criteria.
2. Spec first: the statements in `product/spec/`, `experiments/spec/` or `contributing/spec/` change before anything else.
3. Then a failing test, then the smallest code that passes it, then the trace: each file names the statements it implements, and each statement the files and tests behind it.
4. One draft pull request per issue; CI must be green.
5. Codex reviews it, then a reviewer agent that didn't write it; every thread is answered and resolved before merging.

**Why it suits a team of agents.** Many agents working at once drift: two builders read a requirement differently, a fix quietly undoes another, a result is quoted from a run nobody committed. Here the spec is the source of truth, and every statement is one short sentence with a name. `make spec-check` fails CI when a statement has no code or tests, or a file claims a statement that doesn't exist, so every agent works from the same text and reviewers can check a change against it line by line. Reviews catch the rest, and `make reproduce` keeps every reported number tied to a committed run. The rules are in [`contributing/spec/`](contributing/spec/), and each step of the loop is a skill in [`.agents/skills/`](.agents/skills/). Coding agents start at [AGENTS.md](AGENTS.md).

## Contributing

Issues and pull requests are welcome. Follow the loop above: open an issue, change the spec first, then a failing test and the code, and keep `make lint`, `make test` and `make spec-check` green. Never put API keys in code, configs, logs or commits.

## Citation

```bibtex
@misc{wakelin2026somethingtolose,
  title        = {Something to Lose},
  author       = {Wakelin, Alistair},
  year         = {2026},
  howpublished = {Apart AI Collusion Research Sprint},
  url          = {https://github.com/al-beton/something-to-lose-apart-ai-collusion}
}
```

## License

MIT. See [LICENSE](LICENSE).
