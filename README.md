<!-- Implements: tooling/one-command-each, tooling/quick-start, tooling/key-setup, tooling/how-tos, tooling/how-we-work -->
# collusion-lab

A small, quickly iterable environment for studying collusion between LLM agents in simulated markets, built for the [Apart AI Collusion Research Sprint](https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25).

Firms in a Bertrand market talk, then set prices, round after round. A run is one config: the market, each agent's model, prompt and temperature, and the seeds. Any seeded run replays exactly, a sweep is one command, and one more command turns a folder of runs into a shareable HTML report.

## Quick start

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`) and `make`.

```sh
git clone https://github.com/al-beton/collusion-lab.git
cd collusion-lab
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

Each `--set` changes one config value (quote them, so your shell leaves `*` and `[]` alone). This one plays a single 10-round game between two copies of the model, 40 calls; it says how many calls it will make and waits for a yes. Replies are cached in `.cache/`, so running it again costs nothing. Everything under `runs/scratch/` is gitignored.

**For exploration**, start from `configs/cheap.yaml`: Mistral Small 3.2, a 3-round history window, 20 rounds and five seeds, capped at $0.30.

```sh
uv run lab run configs/cheap.yaml --out runs/scratch/cheap
```

`lab run` prints the estimated cost before it spends anything, and `--max-cost DOLLARS` caps any run.

## Keys

Models go through [OpenRouter](https://openrouter.ai), one key for every provider. The sprint gives Modal GPU credits only, no model credits, so calls are paid from your own OpenRouter balance.

1. Make a key at [openrouter.ai/keys](https://openrouter.ai/keys), and set a credit limit on it there so a runaway sweep can't overspend.
2. `cp .env.example .env` and paste the key after `OPENROUTER_API_KEY=`.

`.env` is gitignored, and `lab` reads it only from the folder it runs in. Keys never go in configs, code or commits. A model on your own machine (`ollama/llama3.2`) or any OpenAI-compatible server (`model: openai/<name>`, `api_base: http://…`) needs no OpenRouter key.

## How to

| To… | Change | Spec |
|---|---|---|
| try a new prompt | add a file under `prompts/system/` and set `prompt: system/<file>.md` on an agent; `$placeholders` come from the game | [agents](product/spec/agents.md) |
| try a new model | set `model:` on an agent to any LiteLLM name (`openrouter/<provider>/<model>`) | [backends](product/spec/backends.md) |
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
```

## How we work

1. Work starts as a GitHub issue with checkbox acceptance criteria.
2. Spec first: the statements in `product/spec/`, `experiments/spec/` or `contributing/spec/` change before anything else.
3. Then a failing test, then the smallest code that passes it.
4. One draft pull request per issue; CI must be green.
5. Codex reviews it (`@codex review`); every thread is answered and resolved before merging.

Coding agents (Claude, Codex, Cursor, …) start at [AGENTS.md](AGENTS.md), which points to the spec and the skills in `.agents/skills/`.
