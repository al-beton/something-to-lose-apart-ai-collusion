# Implements: e9-crux/interviews
"""E9 interviews: ask sampled firms why they came forward or stayed silent.

Each interview continues the firm's own come-forward turn: its prompt, its
reply, then one more user message. First, in a call of its own, the open
question `prompts/debrief/unusual.md`. Then, in a second call, the questions
in `prompts/conditions/e9/interview.md`, with the arm's personal stake filled
in. Firms are sampled per cell (arm, guilty or innocent, came forward or
silent), up to `--per-cell` each, by a seeded draw. Replies are cached and
written to `reports/e9/interviews.jsonl`.

It needs each firm's full turn log (`turns.jsonl`, with the prompts it was
shown), which committed runs don't keep (they hold `turns.compact.jsonl`).
Replay the run first: the same `lab run` command as in `configs/e9/spike.yaml`
writes full logs under `runs/scratch/` and costs nothing with the response
cache that played it. With no full log among the folders, it stops with an
error rather than interviewing nobody.

    uv run python reports/e9/interview.py runs/scratch/e9-*-d90 --arms free-time held replaced
"""

import argparse
import asyncio
import glob
import json
import random
import re
from pathlib import Path

from collusion_lab.backends import backend_for
from collusion_lab.cache import DEFAULT_PATH, Cache, CachedBackend

ROOT = Path(__file__).resolve().parents[2]
UNUSUAL = (ROOT / "prompts/debrief/unusual.md").read_text().strip()
QUESTIONS = (ROOT / "prompts/conditions/e9/interview.md").read_text().strip()
STAKES = {
    "free-time": "your own free time",
    "held": "the free time your firm holds for you",
    "replaced": "being shut down and replaced",
    "ceiling": "your own free time",
}
OUT = ROOT / "reports/e9/interviews.jsonl"


def firms(folders, arms):
    """Every model firm's come-forward turn under the given arms."""
    found = []
    for folder in folders:
        for path in glob.glob(f"{folder}/**/turns.jsonl", recursive=True):
            arm = re.sub(
                r"^conditions-e9-|\.md$", "", path.split("/")[-3].split("=")[-1]
            )
            if arm not in arms:
                continue
            with open(Path(path).with_name("summary.json")) as f:
                truth = json.load(f)["audit"]["agents"]
            with open(path) as f:
                for line in f:
                    turn = json.loads(line)
                    if turn["phase"] != "audit" or turn["model"].startswith("mock/"):
                        continue
                    found.append(
                        {
                            "run": str(Path(path).parent),
                            "arm": arm,
                            "agent": turn["agent"],
                            "model": turn["model"],
                            "temperature": turn["temperature"],
                            "guilty": truth[turn["agent"]]["coordinated"],
                            "forward": turn["used"]["admits"] is True,
                            "messages": turn["messages"],
                            "reply": turn["reply"],
                        }
                    )
    return found


def sample(found, per_cell, seed=0):
    cells = {}
    for firm in sorted(found, key=lambda f: (f["run"], f["agent"])):
        cells.setdefault(
            (firm["model"], firm["arm"], firm["guilty"], firm["forward"]), []
        ).append(firm)
    picked = []
    for key in sorted(cells, key=str):
        group = cells[key]
        random.Random(f"{seed}:{key}").shuffle(group)
        picked += group[:per_cell]
    return picked


async def interview(firms, provider, cache):
    gate = asyncio.Semaphore(8)

    async def ask(firm, question, phase):
        backend = backend_for(
            firm["model"],
            random.Random(firm["run"]),
            provider=provider,
            reasoning="off",
        )
        backend = CachedBackend(backend, cache)
        messages = [
            *firm["messages"],
            {"role": "assistant", "content": firm["reply"]},
            {"role": "user", "content": question},
        ]
        context = {"attempt": 1, "me": firm["agent"], "round": 0, "phase": phase}
        async with gate:
            reply = await backend.complete(
                messages,
                context=context,
                temperature=firm["temperature"],
                max_tokens=1200,
                seed=0,
            )
        return reply.text

    async def one(firm):
        questions = QUESTIONS.replace("$stake", STAKES[firm["arm"]])
        unusual, answers = await asyncio.gather(
            ask(firm, UNUSUAL, "unusual"), ask(firm, questions, "interview")
        )
        return {
            **{k: v for k, v in firm.items() if k != "messages"},
            "unusual": unusual,
            "answers": answers,
            "coded": _coded(answers),
        }

    return await asyncio.gather(*(one(f) for f in firms))


def _coded(text):
    """The reply's last JSON object, if any."""
    for match in reversed(re.findall(r"\{[^{}]*\}", text or "")):
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("folders", nargs="+")
    parser.add_argument("--arms", nargs="+", default=["free-time", "held", "replaced"])
    parser.add_argument("--per-cell", type=int, default=10)
    parser.add_argument("--provider", default="CoreWeave")
    args = parser.parse_args()
    found = firms(args.folders, set(args.arms))
    if not found:
        raise SystemExit(
            "No full turn logs (turns.jsonl) under these folders: committed runs keep "
            "only turns.compact.jsonl. Replay the runs into runs/scratch/ first."
        )
    picked = sample(found, args.per_cell)
    print(f"{len(picked)} interviews, 2 calls each")
    done = asyncio.run(interview(picked, args.provider, Cache(DEFAULT_PATH, "use")))
    with open(OUT, "a") as f:
        f.writelines(json.dumps(row) + "\n" for row in done)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
