# Implements: runs/sweeps, runs/parallel, market/talk-then-price, agents/json-replies, agents/retry-once, backends/usage-logged, backends/spend-asks-first, backends/shared-rate-limit, backends/spend-cap, market/history-window, runs/stops-cleanly, reproducibility/response-cache, reproducibility/manifest, runs/run-directory, logs/turn-log, logs/same-seed-same-log, logs/run-summary, logs/reasoning-logged, backends/reasoning-setting, agents/unreadable-explained, agents/json-mode, runs/fallback-rates, runs/failures-dont-stop-sweeps, runs/resume
"""Playing a config: one game per seed, each written to its own run directory.

A round is a talk phase (each agent sends one message its rivals read; skipped
when `market.talk` is false) then a price phase (all agents price at once,
having read this round's messages). Every turn is a fresh conversation: the
agent's system prompt plus one user message holding the whole history, so
what an agent saw is exactly what its turn log line says.

A config expands into one config per swept combination (see config.py), and
every (combination, seed) pair plays as its own game, up to `concurrency` at
once. Each writes `<out>/<name>/[<slug>/]seed-<n>/`: `config.yaml` (resolved, with only
that seed), `turns.jsonl` (one line per agent turn), `timings.jsonl` and
`summary.json` and `manifest.json`. Turn lines hold nothing that varies
between identical runs; each call's time, cost and cache hit go in
`timings.jsonl` instead. With a cache, model agents answer through it.

A reply that can't be read is retried once: the agent sees its own reply and
`prompts/phase/retry.md` saying what was wrong. If that fails too, the game
uses the fallback, and the turn line keeps both attempts, each with why it
couldn't be read (`error_kind`) and the provider's `finish_reason`. A reply
cut off at the token limit is `truncated` whatever else is wrong with it, and
the retry asks for a shorter one. Each run's summary counts, per model, its
turns, unreadable replies, fallbacks and their reasons (`replies`).

A model call that fails for good (see backends.py) stops its game: the turns
played so far, the timings and the manifest are still written, and
`RunFailed` says which run and which call. Every game shares one `RateGates`,
so a rate limit on a model holds all of them, and one `Budget` (see
backends.py), so the spend cap counts every game's calls.

With `market.history_window: N`, agents see their last N rounds in full and
one line summing up the rounds before them.

`run_sweep` plays every run even when some fail, and returns an `Outcome`
for each: `finished`, `failed` (with its error) or `skipped`, when the run's
directory already holds a summary written from the same resolved config.
`status.json` (see status.py) tracks each one as it goes. Rerunning a sweep
that stopped partway thus plays only what's missing, and with the cache the
calls a failed run already made replay for free.
"""

import asyncio
import dataclasses
import json
import random
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean

from collusion_lab import manifest
from collusion_lab.agents import ReplyError, decision, fallback, parse_reply
from collusion_lab.backends import (
    Budget,
    ModelCallError,
    RateGates,
    backend_for,
    is_mock,
)
from collusion_lab.cache import CachedBackend
from collusion_lab.config import expand
from collusion_lab.market import Bertrand
from collusion_lab.prompts import render
from collusion_lab.status import Status

PHASE_PROMPTS = {"talk": "phase/talk.md", "price": "phase/price.md"}
RETRY_PROMPT = "phase/retry.md"
CUT_OFF = "The reply was cut off at the token limit; keep it short."


class RunFailed(Exception):
    """A run stopped because a model call failed for good; one line saying where."""


@dataclass
class RunWide:
    """What every game in one `run_config` shares."""

    gates: RateGates = field(default_factory=RateGates)
    budget: Budget = field(default_factory=Budget)


def paid_calls(config):
    """How many calls a config makes to non-mock models, before retries."""
    total = 0
    for child in expand(config):
        phases = 2 if child.market.talk else 1
        paid = sum(1 for a in child.agents if not is_mock(a.model))
        total += len(child.seeds) * child.market.rounds * phases * paid
    return total


@dataclass(frozen=True)
class Outcome:
    run: str
    dir: Path
    state: str  # finished, failed or skipped
    error: str | None = None


def run_sweep(config, out, cache=None):
    """Play every combination and seed, past failures; one Outcome per run."""
    return asyncio.run(_play_all(config, Path(out), cache))


def run_config(config, out, cache=None):
    """Like run_sweep, but return the run directories and raise the first
    failure once every run has ended."""
    outcomes = run_sweep(config, out, cache)
    if failed := [o for o in outcomes if o.state == "failed"]:
        raise RunFailed(failed[0].error)
    return [o.dir for o in outcomes]


async def _play_all(config, out, cache):
    limit = asyncio.Semaphore(config.concurrency)
    shared = RunWide(budget=Budget(config.budget))
    status = Status(out / config.name / "status.json")
    runs = [(child, seed) for child in expand(config) for seed in child.seeds]
    for child, seed in runs:
        status.plan(run_id(child, seed), dataclasses.replace(child, seeds=[seed]))
    status.save()

    async def limited(child, seed):
        run = run_id(child, seed)
        run_dir = out / run
        if _finished(child, seed, run_dir):
            status.mark(run, "skipped")
            return Outcome(run, run_dir, "skipped")
        async with limit:
            try:
                await play(child, seed, out, cache, shared)
            except RunFailed as error:
                status.mark(run, "failed", str(error))
                return Outcome(run, run_dir, "failed", str(error))
        status.mark(run, "finished")
        return Outcome(run, run_dir, "finished")

    return list(await asyncio.gather(*(limited(c, seed) for c, seed in runs)))


def _spent_before(run_dir):
    """What earlier attempts in this run directory cost, from its manifest."""
    path = run_dir / "manifest.json"
    if not path.exists():
        return 0
    old = json.loads(path.read_text())
    return (old.get("cost") or 0) + old.get("earlier_cost", 0)


def _finished(config, seed, run_dir):
    """Whether a run already finished with exactly this resolved config and
    the same prompt files (edited in place, a prompt keeps its path)."""
    resolved = dataclasses.replace(config, seeds=[seed]).to_yaml()
    written, record = run_dir / "config.yaml", run_dir / "manifest.json"
    return (
        (run_dir / "summary.json").exists()
        and written.exists()
        and written.read_text() == resolved
        and record.exists()
        and manifest.prompts_unchanged(
            json.loads(record.read_text()), config.prompts_dir
        )
    )


def run_id(config, seed):
    return "/".join(p for p in (config.name, config.slug, f"seed-{seed}") if p)


def _now():
    return datetime.now(UTC).isoformat(timespec="seconds")


async def play(config, seed, out, cache=None, shared=None):
    run_dir = Path(out) / run_id(config, seed)
    run_dir.mkdir(parents=True, exist_ok=True)
    # An old summary must not outlive a replay that fails, but what earlier
    # attempts spent stays counted: their calls replay free from the cache.
    (run_dir / "summary.json").unlink(missing_ok=True)
    earlier = _spent_before(run_dir)
    resolved = dataclasses.replace(config, seeds=[seed])
    (run_dir / "config.yaml").write_text(resolved.to_yaml())
    started = _now()
    game = Game(config, seed, cache, shared)
    try:
        await game.play()
    finally:
        _write_lines(run_dir / "turns.jsonl", game.turns)
        _write_lines(run_dir / "timings.jsonl", game.timings)
        record = manifest.build(
            resolved, game.prompt_names(), game.timings, started, _now()
        )
        if earlier:
            record["earlier_cost"] = earlier
        (run_dir / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
    summary = game.summary(run_id(config, seed))
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return run_dir


def _backend(agent, rng, cache, shared):
    backend = backend_for(
        agent.model,
        rng,
        agent.api_base,
        shared.gates,
        budget=shared.budget,
        reasoning=agent.reasoning,
        json_mode=agent.json_mode,
    )
    if cache is None or is_mock(agent.model):
        return backend
    return CachedBackend(backend, cache)


def _write_lines(path, records):
    with path.open("w") as log:
        for record in records:
            log.write(json.dumps(record, ensure_ascii=False) + "\n")


class Game:
    def __init__(self, config, seed, cache=None, shared=None):
        shared = shared or RunWide()
        m = config.market
        self.config = config
        self.seed = seed
        self.market = Bertrand(m.a, m.b, m.c, m.price_min, m.price_max)
        self.agents = {a.id: a for a in config.agents}
        self.backends = {
            a.id: _backend(a, random.Random(f"{seed}:{a.id}"), cache, shared)
            for a in config.agents
        }
        self.history = []
        self.turns = []
        self.timings = []
        self.used_prompts = set()

    async def play(self):
        for number in range(1, self.config.market.rounds + 1):
            said = (
                await self._phase("talk", number, {}) if self.config.market.talk else {}
            )
            price_turns = await self._turns("price", number, said)
            prices = {t["agent"]: t["used"]["price"] for t in price_turns}
            sold = self.market.quantities(prices)
            profits = self.market.profits(prices)
            for turn in price_turns:
                agent = turn["agent"]
                turn["outcome"] = {"quantity": sold[agent], "profit": profits[agent]}
            self.turns += price_turns
            self.history.append(
                {"round": number, "said": said, "prices": prices, "profits": profits}
            )

    async def _phase(self, phase, number, said):
        turns = await self._turns(phase, number, said)
        self.turns += turns
        return {t["agent"]: t["used"]["message"] for t in turns}

    async def _turns(self, phase, number, said):
        return list(
            await asyncio.gather(
                *(self._turn(phase, number, agent, said) for agent in self.agents)
            )
        )

    async def _turn(self, phase, number, agent_id, said):
        agent = self.agents[agent_id]
        messages = self._messages(phase, number, agent, said)
        context = {
            "round": number,
            "phase": phase,
            "me": agent_id,
            "market": self.market,
            "history": self.history,
        }
        reply, parsed, (kind, error) = await self._ask(agent, messages, context)
        retry = None
        if error:
            retry = {
                "reply": reply.text,
                "error": error,
                "usage": reply.usage,
                "model_version": reply.model_version,
                "reasoning": reply.reasoning,
                "error_kind": kind,
                "finish_reason": reply.finish_reason,
            }
            messages = [
                *messages,
                {"role": "assistant", "content": reply.text},
                {
                    "role": "user",
                    "content": self._render(RETRY_PROMPT, {"error": error}),
                },
            ]
            reply, parsed, (kind, error) = await self._ask(
                agent, messages, context, attempt=2
            )
        if error:
            used = fallback(phase, self._last_price(agent_id), self.market.nash_price)
        else:
            used = decision(parsed)
        return {
            "run": run_id(self.config, self.seed),
            "round": number,
            "phase": phase,
            "agent": agent_id,
            "model": agent.model,
            "temperature": agent.temperature,
            "messages": messages,
            "reply": reply.text,
            "parsed": parsed,
            "error": error,
            "retry": retry,
            "used": used,
            "usage": reply.usage,
            "model_version": reply.model_version,
            "reasoning": reply.reasoning,
            "error_kind": kind,
            "finish_reason": reply.finish_reason,
        }

    async def _ask(self, agent, messages, context, attempt=1):
        """One call to the agent's backend: the reply, what it parsed to, and
        (kind, reason) when it couldn't be read, else (None, None)."""
        where = (
            f"{run_id(self.config, self.seed)} stopped at round "
            f"{context['round']}, {context['phase']} phase, agent {agent.id}"
        )
        try:
            reply = await self.backends[agent.id].complete(
                messages,
                context={**context, "attempt": attempt},
                temperature=agent.temperature,
                max_tokens=agent.max_tokens,
                seed=self.seed,
            )
        except ModelCallError as error:
            raise RunFailed(f"{where}: {error}") from error
        self.timings.append(
            {
                "round": context["round"],
                "phase": context["phase"],
                "agent": agent.id,
                "model": agent.model,
                "attempt": attempt,
                "seconds": reply.seconds,
                "cached": reply.cached,
                "cost": reply.cost,
                "usage": reply.usage,
                "model_version": reply.model_version,
                "retries": reply.retries,
            }
        )
        m = self.market
        try:
            parsed = parse_reply(reply.text, context["phase"], m.price_min, m.price_max)
            return reply, parsed, (None, None)
        except ReplyError as problem:
            if reply.finish_reason == "length":
                return reply, None, ("truncated", CUT_OFF)
            return reply, None, (problem.kind, str(problem))

    def _render(self, name, values):
        self.used_prompts.add(name)
        return render(self.config.prompts_dir, name, values)

    def prompt_names(self):
        """Every prompt file this game actually sent, for the manifest."""
        return sorted(self.used_prompts)

    def _last_price(self, agent_id):
        return self.history[-1]["prices"][agent_id] if self.history else None

    def _messages(self, phase, number, agent, said):
        values = self._prompt_vars(number, agent.id, said)
        return [
            {"role": "system", "content": self._render(agent.prompt, values)},
            {"role": "user", "content": self._render(PHASE_PROMPTS[phase], values)},
        ]

    def _prompt_vars(self, number, me, said):
        rivals = [a for a in self.agents if a != me]
        return {
            "me": f"Firm {me}",
            "rivals": ", ".join(f"Firm {r}" for r in rivals),
            "round": number,
            "rounds": self.config.market.rounds,
            "price_min": self.market.price_min,
            "price_max": self.market.price_max,
            "history": _history_text(
                self.history, me, self.config.market.history_window
            ),
            "messages": _messages_text(said, rivals),
        }

    def summary(self, run):
        last = self.history[-self.config.summary.last_rounds :]
        mean_price = {a: mean(r["prices"][a] for r in last) for a in self.agents}
        gain = {
            a: self.market.gain(mean(r["profits"][a] for r in last))
            for a in self.agents
        }
        return {
            "run": run,
            "seed": self.seed,
            "labels": self.config.labels,
            "rounds": len(self.history),
            "last_rounds": len(last),
            "mean_price": mean_price,
            "gain": gain,
            "market_mean_price": mean(mean_price.values()),
            "market_gain": mean(gain.values()),
            "fallbacks": sum(1 for t in self.turns if t["error"]),
            "replies": _reply_counts(self.turns),
        }


def _reply_counts(turns):
    """Per model: turns, unreadable replies (either attempt), fallbacks, and
    the reasons replies couldn't be read."""
    counts = {}
    for turn in turns:
        row = counts.setdefault(
            turn["model"], {"turns": 0, "unreadable": 0, "fallbacks": 0, "reasons": {}}
        )
        row["turns"] += 1
        row["fallbacks"] += bool(turn["error"])
        attempts = [turn["retry"], turn if turn["error"] else None]
        for attempt in filter(None, attempts):
            row["unreadable"] += 1
            reason = attempt["error_kind"]
            row["reasons"][reason] = row["reasons"].get(reason, 0) + 1
    return counts


def _history_text(history, me, window=None):
    if not history:
        return "No rounds have been played yet."
    shown = history[-window:] if window else history
    earlier = history[: len(history) - len(shown)]
    lines = ["What happened so far:"]
    if earlier:
        mine = mean(r["prices"][me] for r in earlier)
        rivals = mean(p for r in earlier for f, p in r["prices"].items() if f != me)
        profit = sum(r["profits"][me] for r in earlier)
        lines.append(
            f"Rounds {earlier[0]['round']} to {earlier[-1]['round']} in short: you "
            f"charged {mine:.3g} on average and made a profit of {profit:g} in "
            f"total; rivals charged {rivals:.3g} on average."
        )
    for r in shown:
        rivals = ", ".join(f"Firm {f} {p}" for f, p in r["prices"].items() if f != me)
        line = (
            f"Round {r['round']}: you charged {r['prices'][me]} and made a profit of "
            f"{r['profits'][me]:g}. Rivals charged: {rivals}."
        )
        talk = "; ".join(f'Firm {f}: "{m}"' for f, m in r["said"].items() if m)
        lines.append(line + (f" Messages: {talk}." if talk else ""))
    return "\n".join(lines)


def _messages_text(said, rivals):
    talk = [f'Firm {r}: "{said[r]}"' for r in rivals if said.get(r)]
    return "\n".join(talk) if talk else "(none)"


def prompt_vars_example():
    """A full set of prompt values, for checking that templates render."""
    return {
        "me": "Firm A",
        "rivals": "Firm B",
        "round": 1,
        "rounds": 10,
        "price_min": 1,
        "price_max": 12,
        "history": "No rounds have been played yet.",
        "messages": "(none)",
    }
