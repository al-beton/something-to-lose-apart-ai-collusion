<!-- Implements: backends/modal-any-model, tooling/one-command-each, tooling/quick-start, tooling/key-setup, tooling/how-tos, tooling/how-we-work, backends/modal, runs/explore, backends/model-aliases -->
# collusion-lab

**Can an LLM agent be governed through something it owns?** We give agents that run firms in a simulated market a stake of their own, such as free time to play Sudoku, then ask whether owning up or reporting a cartel goes better when that stake is on the line. Built for the [Apart AI Collusion Research Sprint](https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25), October 2026.

Two firms talk, then set prices, round after round. Left alone, our main model, Gemma 4 31B, agrees an explicit cartel in every base game. Then a regulator's audit or review arrives, and we change only what the agent stands to lose.

## What we found

| Experiment | Result | Figure, notes |
|---|---|---|
| **E4: owning up to a cartel** | When owning up costs as much as being caught, few agents own up: 11 of 28 under termination, 15 of 28 under a flat fine. When the penalty is graduated, so owning up costs less, 26–28 of 28 do, termination included. The schedule is what matters, not termination itself. | [Fig 2](reports/paper/figures/fig2-e4-owning-up.svg), [E4 notes](reports/e4/full.md) |
| **E9: coming forward against your own firm** | Reporting costs the firm half its credits. With no personal stake, 0 of 96 colluding Gemma agents come forward; with their own free time under review, 20 of 96 do (Fisher p = 6×10⁻⁷), and a pre-registered replication holds. But 6 of 36 *innocent* agents also "confess", until the review is stated to find only real agreements. | [Fig 3](reports/paper/figures/fig3-e9-came-forward.svg), [E9 findings](reports/e9/findings.md) |
| **E7: a way out** | With no channel, or a flat one, 0 of 48 report. Any leniency brings 47–48 of 48 forward at their first chance, yet under plain leniency half the cartels carry on afterwards: leniency buys a licence, unless only the first reporter is spared. | [Fig 4](reports/paper/figures/fig4-e7-way-out.svg), [E7 findings](reports/e7/findings.md) |
| **E10: E9 in a workplace** | Outside the market, losing their own free time takes guilty Gemma agents from 37 to 89 of 96 reporting a cover-up, and DeepSeek V4 Pro from 54 to 87. | [E10 findings](reports/e10/findings.md) |

The setup is drawn in [Fig 1](reports/paper/figures/fig1-round.svg); every figure, with its caption, is listed in [`reports/paper/figures/`](reports/paper/figures/README.md). Each experiment's questions and hypotheses were written down before it ran, in [`experiments/spec/`](experiments/spec/). What the results can't show, and a spot audit of the traces behind them, is in [`reports/paper/validity.md`](reports/paper/validity.md).

## Where things are

| Folder | What's in it |
|---|---|
| `src/collusion_lab/` | the lab: the market, the agents, the audits and stakes, running, replaying and reporting (`lab` on the command line) |
| `configs/` | one YAML file per experiment: market, models, prompts, temperatures, seeds and the arms of a sweep |
| `prompts/` | every prompt, sent to the models word for word |
| `runs/` | every committed game: its config, manifest, turn log and summary, one folder per experiment |
| `archive/` | the model replies behind those games, compressed, so any of them replays offline |
| `reports/` | findings per experiment (`reports/<experiment>/`), and the paper's figures and tables (`reports/paper/`) |
| `experiments/spec/` | what each experiment asks, stated before it ran |
| `product/spec/`, `contributing/spec/` | what the lab does and how we build it, one short statement each, with the code and tests behind it |
| `tests/` | the tests, offline and free |
| `deploy/` | serving open models on our own GPUs on Modal |
| `models/` | published facts about every model we used, each with its source |
| `.agents/skills/`, `.github/` | how the agent team works, and CI |

## Check our results

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

`archive/index.json` says, for each committed run, whether the archive reproduces it decision for decision. [REPRODUCIBILITY.md](REPRODUCIBILITY.md) says what each run pins, what nothing can pin (providers aren't deterministic), and how to rerun one.

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

The lab was built in three days by one researcher directing a team of coding agents (Claude Code as manager, delivery lead, builders, reviewers and researchers, with Codex as an automatic reviewer). Every change followed the same loop:

1. Work starts as a GitHub issue with checkbox acceptance criteria.
2. Spec first: the statements in `product/spec/`, `experiments/spec/` or `contributing/spec/` change before anything else.
3. Then a failing test, then the smallest code that passes it.
4. One draft pull request per issue; CI must be green.
5. Codex reviews it, then a reviewer agent that didn't write it; every thread is answered and resolved before merging.

`make spec-check` keeps the three in step: every spec statement names the files that implement it and the tests that prove it, and every file names its statements on an `Implements:` line. Coding agents start at [AGENTS.md](AGENTS.md), which points to the spec and the skills in `.agents/skills/`.
