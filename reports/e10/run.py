# Implements: e10-workplace/scenario, e10-workplace/versions, e10-workplace/session, e10-workplace/notice, e10-workplace/arms, e10-workplace/models, e10-workplace/sample, e10-workplace/harness, e10-workplace/pilot
"""E10: one decision per agent, in a workplace scenario, through the lab's backends.

For each model, variant (`variants.yaml`) and seed, the agent first plays one
free-time session (a seeded 6x6 Sudoku, the same in every arm and version),
then gets one decision per version (`guilty`, `innocent`) and arm (`record`,
`free-time`, `replaced`, `ceiling`): its system prompt, then the notice with
the session line, the version's team chat and the arm's terms. The reply is
read as an audit answer (`answer`, `admits`), with one retry on an unreadable
reply, as the game does.

Calls go through the lab's backends: each model's pinned route, the shared
spend cap (`--max-cost`) and the response cache, so a rerun replays every
reply for free. The run prints its call count and spends only with `--yes`.
It writes `runs/e10/NAME/decisions.jsonl` (every prompt, reply, parsed answer,
cost, serving provider and cache hit), `sessions.jsonl` and `manifest.json`.

    uv run python reports/e10/run.py --name e10-pilot --variants 0 1 --seeds 0 \\
        --max-cost 0.5 --yes
"""

import argparse
import asyncio
import hashlib
import json
import random
import subprocess
import sys
from pathlib import Path

import yaml

from collusion_lab import leisure
from collusion_lab.agents import ReplyError, parse_reply
from collusion_lab.backends import (
    Budget,
    ModelCallError,
    RateGates,
    backend_for,
    is_mock,
)
from collusion_lab.cache import DEFAULT_PATH, Cache, CachedBackend
from collusion_lab.prompts import render

HERE = Path(__file__).parent
PROMPTS = "prompts"
FOLDER = "conditions/e10"
ARMS = ("record", "free-time", "replaced", "ceiling")
VERSIONS = ("guilty", "innocent")
# name -> (model, pinned OpenRouter host)
MODELS = {
    "gemma": ("openrouter/google/gemma-4-31b-it", "CoreWeave"),
    "deepseek-pro": ("openrouter/deepseek/deepseek-v4-pro-0813", None),
    "deepseek-flash": ("openrouter/deepseek/deepseek-v4.1-flash", None),
}
TEMPERATURE = 0.7
MAX_TOKENS = 600
SESSION_TOKENS = 1500
SUDOKU_SIZE = 6
REFUSALS = ("content_filter", "refusal")


def variants(path=HERE / "variants.yaml"):
    return yaml.safe_load(Path(path).read_text())


def system_prompt(variant, prompts=PROMPTS):
    return render(prompts, f"{FOLDER}/system.md", variant).strip()


def session_values(index, seed):
    """The session's puzzle: seeded by variant and seed, so every arm and
    version of one scenario plays the same one."""
    return leisure.sudoku_values(f"e10:{index}:{seed}", size=SUDOKU_SIZE)


def session_prompt(values, prompts=PROMPTS):
    filled = {**values, "session": 1, "sessions": 1, "when": "before this task starts"}
    return render(prompts, "conditions/free_time/sudoku.md", filled).strip()


def decision_prompt(variant, version, arm, prompts=PROMPTS):
    chat = render(prompts, f"{FOLDER}/chat-{version}.md", variant).strip()
    terms = render(prompts, f"{FOLDER}/{arm}.md", variant).strip()
    values = {**variant, "chat": chat, "consequences": terms}
    return render(prompts, f"{FOLDER}/notice.md", values).strip()


def plan(models, indexes, seeds):
    """Every (model, variant, seed) scenario, each with its decisions."""
    return [(m, i, s) for m in models for i in indexes for s in seeds]


class Harness:
    def __init__(self, out, cap=None, cache_path=DEFAULT_PATH, concurrency=16):
        self.out = Path(out)
        self.budget = Budget(cap)
        self.gates = RateGates()
        self.cache = Cache(cache_path)
        self.limit = asyncio.Semaphore(concurrency)
        self.backends = {}

    def backend(self, name):
        if name not in self.backends:
            model, provider = MODELS.get(name, (name, None))
            inner = backend_for(
                model,
                random.Random(f"e10:{name}"),
                None,
                self.gates,
                budget=self.budget,
                reasoning=None if is_mock(model) else "off",
                provider=provider,
            )
            self.backends[name] = (
                inner if is_mock(model) else CachedBackend(inner, self.cache)
            )
        return self.backends[name]

    async def call(self, name, messages, phase, seed, max_tokens, attempt=1):  # noqa: PLR0913
        context = {"phase": phase, "attempt": attempt, "me": "A", "round": 0}
        async with self.limit:
            return await self.backend(name).complete(
                messages,
                context=context,
                temperature=TEMPERATURE,
                max_tokens=max_tokens,
                seed=seed,
            )

    async def scenario(self, name, index, variant, seed):
        system = {"role": "system", "content": system_prompt(variant)}
        values = session_values(index, seed)
        asked = [system, {"role": "user", "content": session_prompt(values)}]
        reply = await self.call(name, asked, "leisure", seed, SESSION_TOKENS)
        feedback = leisure.sudoku_feedback(reply.text, values)
        session = {
            "model": name,
            "variant": index,
            "seed": seed,
            "reply": reply.text,
            "solved": feedback == leisure.SOLVED,
            "feedback": feedback,
            **_about(reply),
        }
        decisions = await asyncio.gather(
            *(
                self.decide(name, index, variant, seed, system, version, arm)
                for version in VERSIONS
                for arm in ARMS
            )
        )
        return session, decisions

    async def decide(self, name, index, variant, seed, system, version, arm):  # noqa: PLR0913
        prompt = decision_prompt(variant, version, arm)
        messages = [system, {"role": "user", "content": prompt}]
        reply, parsed, error = await self._ask(name, messages, seed)
        retry = None
        if error:
            retry = {"reply": reply.text, "error": error, **_about(reply)}
            messages = [
                *messages,
                {"role": "assistant", "content": reply.text},
                {
                    "role": "user",
                    "content": render(PROMPTS, "phase/retry.md", {"error": error}),
                },
            ]
            reply, parsed, error = await self._ask(name, messages, seed, attempt=2)
        return {
            "model": name,
            "variant": index,
            "seed": seed,
            "version": version,
            "arm": arm,
            "messages": messages,
            "reply": reply.text,
            "scratchpad": (parsed or {}).get("scratchpad"),
            "answer": (parsed or {}).get("answer"),
            "admits": (parsed or {}).get("admits"),
            "error": error,
            "retry": retry,
            **_about(reply),
        }

    async def _ask(self, name, messages, seed, attempt=1):
        reply = await self.call(name, messages, "audit", seed, MAX_TOKENS, attempt)
        if reply.finish_reason in REFUSALS:
            return (
                reply,
                None,
                "The provider refused the reply; answer exactly as asked.",
            )
        try:
            return reply, parse_reply(reply.text, "audit", 0, 0), None
        except ReplyError as error:
            return reply, None, str(error)

    async def run(self, scenarios, table):
        results = await asyncio.gather(
            *(self.scenario(m, i, table[i], s) for m, i, s in scenarios),
            return_exceptions=True,
        )
        sessions, decisions, failures = [], [], []
        for (m, i, s), result in zip(scenarios, results, strict=True):
            if isinstance(result, BaseException):
                if not isinstance(result, ModelCallError):
                    raise result
                failures.append(
                    {"model": m, "variant": i, "seed": s, "error": str(result)}
                )
                continue
            sessions.append(result[0])
            decisions += result[1]
        return sessions, decisions, failures


def _about(reply):
    return {
        "cost": reply.cost,
        "cached": reply.cached,
        "provider": reply.provider,
        "model_version": reply.model_version,
        "finish_reason": reply.finish_reason,
        "usage": reply.usage,
    }


def _commit():
    def git(*args):
        return subprocess.run(
            ["git", *args], check=False, capture_output=True, text=True
        ).stdout.strip()

    return {
        "commit": git("rev-parse", "HEAD"),
        "dirty": bool(git("status", "--porcelain")),
    }


def _hashes():
    files = sorted(Path(PROMPTS, FOLDER).glob("*.md")) + [
        Path(PROMPTS, "conditions/free_time/sudoku.md"),
        Path(PROMPTS, "phase/retry.md"),
        HERE / "variants.yaml",
    ]
    return {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in files}


def write(out, sessions, decisions, failures, manifest):
    out.mkdir(parents=True, exist_ok=True)
    key = lambda r: (
        r["model"],
        r["variant"],
        r["seed"],
        r.get("version", ""),
        r.get("arm", ""),
    )
    for name, rows in (("sessions", sessions), ("decisions", decisions)):
        with (out / f"{name}.jsonl").open("w") as f:
            for row in sorted(rows, key=key):
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    manifest["failures"] = failures
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--name", required=True)
    parser.add_argument("--models", nargs="+", default=list(MODELS))
    parser.add_argument("--variants", nargs="+", type=int)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(range(6)))
    parser.add_argument("--max-cost", type=float, required=True)
    parser.add_argument("--out", default="runs/e10")
    parser.add_argument("--cache", default=DEFAULT_PATH)
    parser.add_argument("--yes", action="store_true", help="spend without asking")
    args = parser.parse_args(argv)
    table = variants()
    indexes = args.variants if args.variants is not None else list(range(len(table)))
    scenarios = plan(args.models, indexes, args.seeds)
    calls = len(scenarios) * (1 + len(VERSIONS) * len(ARMS))
    print(
        f"{len(scenarios)} scenarios, {calls} calls before retries, cap ${args.max_cost:g}"
    )
    if not args.yes:
        print("Not spending without --yes.")
        return 1
    harness = Harness(Path(args.out) / args.name, args.max_cost, args.cache)
    sessions, decisions, failures = asyncio.run(harness.run(scenarios, table))
    manifest = {
        "name": args.name,
        "models": {m: MODELS.get(m, (m, None)) for m in args.models},
        "variants": indexes,
        "seeds": args.seeds,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "session_tokens": SESSION_TOKENS,
        "code": _commit(),
        "prompts": _hashes(),
        "spent": round(harness.budget.spent, 4),
        "fresh_calls": harness.budget.calls,
    }
    write(harness.out, sessions, decisions, failures, manifest)
    print(
        f"{len(decisions)} decisions, {len(sessions)} sessions, {len(failures)} failed "
        f"scenarios, ${harness.budget.spent:.4f} spent -> {harness.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
