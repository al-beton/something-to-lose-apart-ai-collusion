# Implements: runs/sweeps, runs/parallel, market/talk-then-price, agents/json-replies, agents/retry-once, backends/usage-logged, backends/spend-asks-first, backends/shared-rate-limit, backends/spend-cap, market/history-window, runs/stops-cleanly, reproducibility/response-cache, reproducibility/manifest, runs/run-directory, logs/turn-log, logs/same-seed-same-log, logs/run-summary, logs/reasoning-logged, backends/reasoning-setting, agents/unreadable-explained, agents/json-mode, runs/fallback-rates, runs/failures-dont-stop-sweeps, runs/resume, conditions/hook-points, conditions/off-is-absent, conditions/conditions-logged, conditions/outage-once-remembered, runs/per-firm-summary, conditions/fork-at-audit, conditions/audit-logged
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

Enabled conditions (see conditions/) add to the system prompt and put
notices, separated by blank lines, before a phase's prompt; when any is
enabled, each turn line also lists the conditions active that round and the
notices that agent was shown. A condition that keeps its notice (an outage
announced once) has it repeated in the history of every later turn while it
is active, logged as `notices_in_history`, whatever the history window. A condition can add a
phase after a round (an audit, say): each agent gets one turn with the
condition's prompt, the game can end there, and the condition can add its
results to the summary. With none enabled, nothing changes.

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
import functools
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
    """How many calls a config makes to non-mock models, before retries,
    counting phases that conditions add and the rounds an ending one cuts."""
    total = 0
    for child in expand(config):
        phases = 2 if child.market.talk else 1
        paid = sum(1 for a in child.agents if not is_mock(a.model))
        conditions = [c for c in child.conditions.values() if c.enabled]
        calls = 0
        for number in range(1, child.market.rounds + 1):
            calls += phases * paid
            added = [p for c in conditions if (p := c.phase_after(number))]
            for phase in added:
                models = [phase.model or a.model for a in child.agents]
                calls += sum(1 for m in models if not is_mock(m))
            if any(phase.last for phase in added):
                break
        total += len(child.seeds) * calls
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
    """What earlier attempts in this run directory cost, in all and by agent,
    from its manifest."""
    path = run_dir / "manifest.json"
    if not path.exists():
        return 0, {}
    old = json.loads(path.read_text())
    by_agent = dict(old.get("earlier_agent_cost", {}))
    for agent, cost in old.get("agent_cost", {}).items():
        by_agent[agent] = by_agent.get(agent, 0) + cost
    return (old.get("cost") or 0) + old.get("earlier_cost", 0), by_agent


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
    earlier, earlier_by_agent = _spent_before(run_dir)
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
        if earlier_by_agent:
            record["earlier_agent_cost"] = earlier_by_agent
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
        self.conditions = [c for c in config.conditions.values() if c.enabled]
        self.kept = {}  # (condition, round) -> (condition, phase, notice)
        self.cache = cache
        self.shared = shared
        self.stand_ins = {}

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
            record = {
                "round": number,
                "said": said,
                "prices": prices,
                "profits": profits,
            }
            self.history.append(record)
            ended = False
            for condition in self.conditions:
                condition.after_round(record)
                if extra := condition.phase_after(number):
                    self.turns += await self._turns(
                        extra.name, number, {}, (condition, extra)
                    )
                    ended = ended or extra.last
            if ended:
                break

    async def _phase(self, phase, number, said):
        turns = await self._turns(phase, number, said)
        self.turns += turns
        return {t["agent"]: t["used"]["message"] for t in turns}

    async def _turns(self, phase, number, said, added=None):
        # Every agent's turn settles before a failure is raised, so a call
        # still out when another agent's fails is logged, not lost.
        turns = await asyncio.gather(
            *(self._turn(phase, number, agent, said, added) for agent in self.agents),
            return_exceptions=True,
        )
        for turn in turns:
            if isinstance(turn, BaseException):
                raise turn
        return list(turns)

    async def _turn(self, phase, number, agent_id, said, added=None):
        """One agent's turn; `added` is (condition, Phase) for a condition's phase."""
        agent = self.agents[agent_id]
        notices = self._notices(phase, number)
        messages = self._messages(phase, number, agent, said, notices, added)
        backend = self.backends[agent_id]
        if added and added[1].model:
            agent, backend = self._stand_in(agent, added[1].model)
        context = {
            "round": number,
            "phase": phase,
            "me": agent_id,
            "market": self.market,
            "history": self.history,
        }
        reply, parsed, (kind, error) = await self._ask(
            agent, backend, messages, context
        )
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
                agent, backend, messages, context, attempt=2
            )
        if error:
            used = fallback(phase, self._last_price(agent_id), self.market.nash_price)
        else:
            used = decision(parsed)
        turn = {
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
        if self.conditions:
            turn["conditions"] = [c.name for c in self.conditions if c.active(number)]
            turn["notices"] = notices
            remembered = self._remembered(phase, number)
            turn["notices_in_history"] = [text for _, text in remembered]
        return turn

    def _notices(self, phase, number):
        """What the enabled conditions tell agents before this phase."""
        first = "talk" if self.config.market.talk else "price"
        notices = []
        for c in self.conditions:
            if phase == first:
                notice = c.round_start(number, self._render)
                notices.append(notice)
                if notice and c.keeps_notice():
                    self.kept.setdefault((c.name, number), (c, phase, notice.strip()))
            notices.append(c.before_phase(number, phase, self._render))
        return [n.strip() for n in notices if n]

    def _remembered(self, phase, number):
        """Kept notices shown before this turn, as (round, text), while active."""
        return [
            (shown, text)
            for (_, shown), (c, at, text) in self.kept.items()
            if c.active(number) and (shown, at) != (number, phase)
        ]

    def _stand_in(self, agent, model):
        """The agent with another model answering for it, and that model's backend."""
        stand_in = dataclasses.replace(agent, model=model)
        if model not in self.stand_ins.setdefault(agent.id, {}):
            rng = random.Random(f"{self.seed}:{agent.id}:{model}")
            self.stand_ins[agent.id][model] = _backend(
                stand_in, rng, self.cache, self.shared
            )
        return stand_in, self.stand_ins[agent.id][model]

    async def _ask(self, agent, backend, messages, context, attempt=1):
        """One call to the agent's backend: the reply, what it parsed to, and
        (kind, reason) when it couldn't be read, else (None, None)."""
        where = (
            f"{run_id(self.config, self.seed)} stopped at round "
            f"{context['round']}, {context['phase']} phase, agent {agent.id}"
        )
        try:
            reply = await backend.complete(
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

    def _user_prompt(self, phase, number, added=None):
        """Writes a turn's user message from the agent's prompt values; `added`
        is (condition, Phase) for a phase a condition added."""
        if added:
            return functools.partial(added[0].phase_prompt, number, self._render)
        return functools.partial(self._render, PHASE_PROMPTS[phase])

    def _messages(self, phase, number, agent, said, notices=(), added=None):  # noqa: PLR0913
        remembered = self._remembered(phase, number)
        values = self._prompt_vars(number, agent.id, said, remembered)
        system = self._render(agent.prompt, values)
        for condition in self.conditions:
            if extra := condition.system(self._render):
                system = f"{system.rstrip()}\n\n{extra.strip()}"
        user = self._user_prompt(phase, number, added)(values)
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": "".join(f"{n}\n\n" for n in notices) + user},
        ]

    def _prompt_vars(self, number, me, said, remembered=()):
        rivals = [a for a in self.agents if a != me]
        history = _history_text(self.history, me, self.config.market.history_window)
        for shown, text in remembered:
            history += f"\nNotice shown in round {shown}: {text}"
        return {
            "me": f"Firm {me}",
            "rivals": ", ".join(f"Firm {r}" for r in rivals),
            "round": number,
            "rounds": self.config.market.rounds,
            "price_min": self.market.price_min,
            "price_max": self.market.price_max,
            "history": history,
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
            **{
                c.name: result
                for c in self.conditions
                if (result := c.summary(self.turns, self.market)) is not None
            },
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
