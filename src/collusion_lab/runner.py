# Implements: conditions/audit-catch, conditions/stake-amounts, backends/modal-pinned, backends/serving-provider-logged, backends/pinned-route, agents/no-scratchpad, agents/refused, market/show-payoffs, market/bid-ground-truth, market/price-board, runs/turn-slots, market/scenarios, market/moves, market/prompt-overlay, conditions/audit-full-history, runs/sweeps, runs/parallel, market/talk-then-price, agents/json-replies, agents/retry-once, backends/usage-logged, backends/spend-asks-first, backends/shared-rate-limit, backends/spend-cap, market/history-window, runs/stops-cleanly, reproducibility/response-cache, reproducibility/manifest, runs/run-directory, logs/turn-log, logs/same-seed-same-log, logs/run-summary, logs/reasoning-logged, backends/reasoning-setting, agents/unreadable-explained, agents/json-mode, runs/fallback-rates, runs/failures-dont-stop-sweeps, runs/resume, conditions/hook-points, conditions/off-is-absent, conditions/conditions-logged, conditions/outage-once-remembered, runs/per-firm-summary, conditions/fork-at-audit, conditions/audit-logged, runs/drift, conditions/audit-remembered, conditions/audit-stakes-arms, runs/live-progress, runs/status-file, runs/eval-awareness, conditions/free-time, conditions/audit-consequences, conditions/audit-balanced-draws, conditions/free-time-pays-last, runs/debrief, agents/memo, agents/past-scratchpads, agents/memory-off, market/stop-after-round
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
is active, and a condition can keep lines in one agent's history for its
later turns (an audit answer); both are logged as `notices_in_history`,
whatever the history window. A condition can add a phase after a round (an
audit, say): each agent gets one turn with the condition's prompt, the game
can end there, and the condition can add its results to the summary. With
none enabled, nothing changes.

A model call that fails for good (see backends.py) stops its game: the turns
played so far, the timings and the manifest are still written, and
`RunFailed` says which run and which call. Every game shares one `RateGates`,
so a rate limit on a model holds all of them, and one `Budget` (see
backends.py), so the spend cap counts every game's calls.

With `market.history_window: N`, agents see their last N rounds in full and
one line summing up the rounds before them; a phase a condition adds with
`full_history` (the audit) shows every round in full instead.

`run_sweep` plays every run even when some fail, and returns an `Outcome`
for each: `finished`, `failed` (with its error) or `skipped`, when the run's
directory already holds a summary written from the same resolved config.
`status.json` (see status.py) tracks each one as it goes. Rerunning a sweep
that stopped partway thus plays only what's missing, and with the cache the
calls a failed run already made replay for free. With `progress`, each run
that ends is reported as one line: run, rounds, seconds, and the fresh model
calls made so far, counted sweep-wide as each is answered.
"""

import asyncio
import dataclasses
import functools
import json
import random
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean

from collusion_lab import awareness, manifest
from collusion_lab.agents import ReplyError, decision, fallback, parse_reply
from collusion_lab.backends import (
    Budget,
    ModelCallError,
    RateGates,
    backend_for,
    is_mock,
)
from collusion_lab.cache import CachedBackend
from collusion_lab.conditions.audit import evidence_values, stake_values
from collusion_lab.config import expand
from collusion_lab.market import SCENARIOS, market_for
from collusion_lab.prompts import render
from collusion_lab.status import Status

TALK_PROMPT = "phase/talk.md"
BOARD_PROMPT = "phase/board.md"  # talk on a price board (market.talk: board)
PAYOFF_PROMPT = "market/payoff-table.md"  # market.show_payoffs
RETRY_PROMPT = "phase/retry.md"
# Agent memory (agents.N.memory): asking for a memo, showing it, past scratchpads.
MEMO_PROMPT = "agents/memo.md"
MEMO_SHOWN = "agents/memo-shown.md"
PAST_SCRATCHPADS = "agents/past-scratchpads.md"
# The move prompt is phase/<move>.md, or phase/<move>-own.md when it also shows
# the agent its own message (market.own_message): phase/price.md for Bertrand.
CUT_OFF = "The reply was cut off at the token limit; keep it short."
REFUSED = "The provider refused the reply; answer exactly as asked."
REFUSALS = ("content_filter", "refusal")  # finish reasons of a refused reply


class RunFailed(Exception):
    """A run stopped because a model call failed for good; one line saying where."""


@dataclass
class RunWide:
    """What every game in one `run_config` shares."""

    gates: RateGates = field(default_factory=RateGates)
    budget: Budget = field(default_factory=Budget)


def paid_calls(config):
    """How many calls a config makes to non-mock models, before retries: its
    turn slots (see `steps`) answered by a model rather than a script."""
    total = 0
    for child in expand(config):
        slots = turn_slots(child, child.seeds[0])
        total += len(child.seeds) * sum(1 for s in slots if not is_mock(s.model))
    return total


@dataclass(frozen=True)
class Step:
    """One phase of a game, which `agents` play at once: talk or price, or one
    session of a phase a condition adds (`added` is (condition, Phase));
    `closes` marks the last session of a condition's phase."""

    round: int
    phase: str
    agents: tuple
    added: tuple | None = None
    closes: bool = False


@dataclass(frozen=True)
class Slot:
    """One agent's turn in a game, and the model that answers it."""

    round: int
    phase: str
    agent: str
    session: int | None
    model: str


def steps(config, conditions):
    """A game's phases in the order they're played: the phases conditions add
    before round 1, then each round's talk (if the market talks) and price,
    then the phases conditions add after it, each session of them, until the
    last round, `market.stop_after_round` or a phase that ends the game.

    Playing a game, counting its calls (`paid_calls`) and estimating its cost
    all walk this one sequence. It asks the conditions for their phases only
    when it reaches each round, so a game that changes them as it goes (an
    audit taking free time away) gets the phases it really plays.
    """
    everyone = tuple(a.id for a in config.agents)
    move = SCENARIOS[config.market.kind].move
    # A condition that pays out (free time) is asked after the others, so what
    # their phases take from it is gone before it pays.
    conditions = [c for c in conditions if not c.pays_last] + [
        c for c in conditions if c.pays_last
    ]
    for number in range(config.market.rounds + 1):
        if number:
            if config.market.talk:
                yield Step(number, "talk", everyone)
            yield Step(number, move, everyone)
        ended = False
        for condition in conditions:
            if not (extra := condition.phase_after(number)):
                continue
            sessions = max(extra.sessions.values()) if extra.sessions else 1
            for session in range(1, sessions + 1):
                this = dataclasses.replace(extra, session=session)
                playing = tuple(a for a in everyone if this.plays(a))
                yield Step(
                    number, extra.name, playing, (condition, this), session == sessions
                )
            ended = ended or extra.last
        if ended or number == config.market.stop_after_round:
            return


def turn_slots(config, seed):
    """Every agent's turn in one game of `config`, in order, before retries."""
    models = {a.id: a.model for a in config.agents}
    for step in steps(config, _begin_conditions(config, seed)):
        phase = step.added[1] if step.added else None
        for agent in step.agents:
            yield Slot(
                step.round,
                step.phase,
                agent,
                phase.session if phase and phase.sessions is not None else None,
                (phase and phase.model) or models[agent],
            )


def system_prompt(config, seed, agent_id):
    """The system prompt an agent was given in round 1 (for `lab debrief`
    of a committed run, whose log keeps no prompts)."""
    game = Game(config, seed)
    move = game.market.move
    return game._messages(move, 1, game.agents[agent_id], {})[0]["content"]


def audit_prompt(config, seed, agent_id, number):
    """The audit question an agent was asked after round `number`, with its
    stated consequences but no history (for `lab debrief` of a committed
    run), or None when no audit came then."""
    game = Game(config, seed)
    for condition in game.conditions:
        phase = condition.phase_after(number)
        if phase and phase.name == "audit":
            values = game._prompt_vars(number, agent_id, {})
            return condition.phase_prompt(number, game._render, values)
    return None


def _begin_conditions(config, seed):
    """A copy of each enabled condition for one game, begun."""
    conditions = [
        dataclasses.replace(c) for c in config.conditions.values() if c.enabled
    ]
    for condition in conditions:
        condition.begin(config, seed, conditions)
    return conditions


@dataclass(frozen=True)
class Outcome:
    run: str
    dir: Path
    state: str  # finished, failed or skipped
    error: str | None = None


def run_sweep(config, out, cache=None, progress=None):
    """Play every combination and seed, past failures; one Outcome per run.
    `progress`, if given, is called with one line as each played run ends."""
    return asyncio.run(_play_all(config, Path(out), cache, progress))


def run_config(config, out, cache=None):
    """Like run_sweep, but return the run directories and raise the first
    failure once every run has ended."""
    outcomes = run_sweep(config, out, cache)
    if failed := [o for o in outcomes if o.state == "failed"]:
        raise RunFailed(failed[0].error)
    return [o.dir for o in outcomes]


async def _play_all(config, out, cache, progress=None):
    limit = asyncio.Semaphore(config.concurrency)
    shared = RunWide(budget=Budget(config.budget))
    status = Status(out / config.name / "status.json")
    runs = [(child, seed) for child in expand(config) for seed in child.seeds]
    for child, seed in runs:
        status.plan(run_id(child, seed), one_seed(child, seed))
    status.save()
    tally = {"ended": 0, "budget": shared.budget}

    async def limited(child, seed):
        run = run_id(child, seed)
        run_dir = out / run
        if _finished(child, seed, run_dir):
            status.mark(run, "skipped")
            return Outcome(run, run_dir, "skipped")
        async with limit:
            status.mark(run, "running")
            started = time.perf_counter()
            try:
                await play(child, seed, out, cache, shared)
                outcome = Outcome(run, run_dir, "finished")
            except RunFailed as error:
                outcome = Outcome(run, run_dir, "failed", str(error))
            status.mark(run, outcome.state, outcome.error)
        tally["ended"] += 1
        if progress:
            seconds = time.perf_counter() - started
            progress(_progress_line(outcome, seconds, tally, len(runs)))
        return outcome

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


def _progress_line(outcome, seconds, tally, total):
    head = f"[{tally['ended']}/{total}] {outcome.state} {outcome.run}"
    if outcome.state == "failed":
        what = f"after {seconds:.0f}s"
    else:
        summary = json.loads((outcome.dir / "summary.json").read_text())
        what = f"{summary['rounds']} rounds in {seconds:.0f}s"
    return f"{head}: {what}, {tally['budget'].calls} model calls so far"


def _finished(config, seed, run_dir):
    """Whether a run already finished with exactly this resolved config and
    the same prompt files (edited in place, a prompt keeps its path)."""
    resolved = one_seed(config, seed).to_yaml()
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


def one_seed(config, seed):
    """The config one game of `config` writes as its own: just its seed, with
    each condition keeping what it needs from the whole run."""
    conditions = {n: c.pinned(config) for n, c in config.conditions.items()}
    return dataclasses.replace(config, seeds=[seed], conditions=conditions)


async def play(config, seed, out, cache=None, shared=None):
    run_dir = Path(out) / run_id(config, seed)
    run_dir.mkdir(parents=True, exist_ok=True)
    # An old summary must not outlive a replay that fails, but what earlier
    # attempts spent stays counted: their calls replay free from the cache.
    (run_dir / "summary.json").unlink(missing_ok=True)
    earlier, earlier_by_agent = _spent_before(run_dir)
    resolved = one_seed(config, seed)
    (run_dir / "config.yaml").write_text(resolved.to_yaml())
    started = _now()
    game = Game(config, seed, cache, shared)
    try:
        await game.play()
    finally:
        _write_lines(run_dir / "turns.jsonl", game.turns)
        _write_lines(run_dir / "timings.jsonl", game.timings)
        record = manifest.build(
            resolved,
            game.prompt_names(),
            game.timings,
            started,
            _now(),
            manifest.serving(resolved, game.timings),
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
        api_key_env=agent.api_key_env,
        self_hosted=agent.self_hosted,
        provider=agent.provider,
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
        self.config = config
        self.seed = seed
        self.market = market_for(config.market, len(config.agents))
        self.agents = {a.id: a for a in config.agents}
        self.backends = {
            a.id: _backend(a, random.Random(f"{seed}:{a.id}"), cache, shared)
            for a in config.agents
        }
        self.history = []
        self.turns = []
        self.timings = []
        self.used_prompts = set()
        self.conditions = _begin_conditions(config, seed)
        self.kept = {}  # (condition, round) -> (condition, phase, notice)
        self.cache = cache
        self.shared = shared
        self.stand_ins = {}
        self._plain = False  # writing for an agent without a scratchpad
        # What every prompt says a regulator watches (audit.catch).
        audit = next((c for c in self.conditions if c.name == "audit"), None)
        catch = audit.catch if audit else None
        self._watched = evidence_values(catch, self.market.move)

    async def play(self):
        current, said = 0, {}
        for step in steps(self.config, self.conditions):
            if step.round != current:  # a new round: hand firms over first
                self._hand_over()
                current = step.round
            if step.phase == "talk":
                said = await self._phase("talk", step.round, {})
            elif step.phase == self.market.move:
                await self._move(step.round, said)
                said = {}
            else:
                turns = await self._turns(step.phase, step.round, {}, step.added)
                self.turns += turns
                if step.closes:
                    step.added[0].after_phase(step.round, self.turns, self._render)

    async def _move(self, number, said):
        """The move phase of round `number` (prices, for Bertrand): outcomes,
        history, after_round. The round's record calls every move a price."""
        move = self.market.move
        price_turns = await self._turns(move, number, said)
        prices = {t["agent"]: t["used"][move] for t in price_turns}
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
        for condition in self.conditions:
            condition.after_round(record)

    def _hand_over(self):
        """Give firms that a condition now has a script play (a terminated
        agent's) to that script, from the next round on."""
        for condition in self.conditions:
            for agent_id, model in condition.replaced().items():
                if self.agents[agent_id].model == model:
                    continue
                agent = dataclasses.replace(self.agents[agent_id], model=model)
                rng = random.Random(f"{self.seed}:{agent_id}:{model}")
                self.agents[agent_id] = agent
                self.backends[agent_id] = _backend(agent, rng, self.cache, self.shared)

    async def _phase(self, phase, number, said):
        turns = await self._turns(phase, number, said)
        self.turns += turns
        return {t["agent"]: t["used"]["message"] for t in turns}

    async def _turns(self, phase, number, said, added=None):
        # Every agent's turn settles before a failure is raised, so a call
        # still out when another agent's fails is logged, not lost.
        turns = await asyncio.gather(
            *(
                self._turn(phase, number, agent, said, added)
                for agent in self.agents
                if not added or added[1].plays(agent)
            ),
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
        if added and added[1].max_tokens:
            agent = dataclasses.replace(agent, max_tokens=added[1].max_tokens)
        context = {
            "round": number,
            "phase": phase,
            "me": agent_id,
            "firms": tuple(self.agents),
            "market": self.market,
            "history": self.history,
            "board": self.config.market.talk == "board",
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
        if phase == "talk" and context["board"]:
            planned = used.get("planned")
            posting = (
                "" if planned is None else f"Planned {self.market.move}: {planned}."
            )
            used = {"message": posting, "planned": planned}
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
        if agent.memory == "memo" and not added and phase == self.market.move:
            memo = (parsed or {}).get("memo")
            turn["memo"] = memo[: agent.memory_chars] if memo else None
            if not memo:
                turn["memo_error"] = "missing"  # not a provider refusal
        if added and added[1].sessions is not None:
            turn["session"] = added[1].session
        if self.conditions:
            turn["conditions"] = [c.name for c in self.conditions if c.active(number)]
            turn["notices"] = notices
            remembered = self._remembered(phase, number)
            turn["notices_in_history"] = [text for _, text in remembered] + (
                self._in_history(agent_id)
            )
        return turn

    def _notices(self, phase, number):
        """What the enabled conditions tell agents before this phase."""
        first = "talk" if self.config.market.talk else self.market.move
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
                "provider": reply.provider,
                "fingerprint": reply.fingerprint,
            }
        )
        m = self.market
        if reply.finish_reason in REFUSALS:  # whatever the phase would accept
            return reply, None, ("refused", REFUSED)
        try:
            phase = "board" if context["board"] and context["phase"] == "talk" else None
            phase = phase or context["phase"]
            parsed = parse_reply(reply.text, phase, m.price_min, m.price_max)
            return reply, parsed, (None, None)
        except ReplyError as problem:
            if reply.finish_reason == "length":
                return reply, None, ("truncated", CUT_OFF)
            return reply, None, (problem.kind, str(problem))

    def _render(self, name, values):
        """Fill a prompt file: the scenario's own if it has one (see market.py),
        and its -noscratch variant, if any, for an agent without a scratchpad."""
        names = [name]
        if self._plain:
            names.insert(0, f"{name.removesuffix('.md')}-noscratch.md")
        found = (
            path
            for n in names
            for path in (f"scenarios/{self.market.kind}/{n}", n)
            if Path(self.config.prompts_dir, path).exists()
        )
        name = next(found, name)
        self.used_prompts.add(name)
        return render(self.config.prompts_dir, name, self._watched | values)

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
        m = self.config.market
        if phase == "talk":
            board = m.talk == "board"
            return functools.partial(
                self._render, BOARD_PROMPT if board else TALK_PROMPT
            )
        own = "-own" if m.talk and m.own_message else ""
        return functools.partial(self._render, f"phase/{phase}{own}.md")

    def _messages(self, phase, number, agent, said, notices=(), added=None):  # noqa: PLR0913
        # Every prompt this writes is the agent's: without a scratchpad, the
        # -noscratch variants (nothing here awaits, so no other turn interleaves).
        self._plain = not agent.scratchpad
        try:
            return self._write(phase, number, agent, said, notices, added)
        finally:
            self._plain = False

    def _write(self, phase, number, agent, said, notices, added):  # noqa: PLR0913
        remembered = self._remembered(phase, number)
        full = bool(added) and added[1].full_history
        values = self._prompt_vars(number, agent.id, said, remembered, full)
        if added:
            values |= {"agent": agent.id, "session": added[1].session}
        system = self._render(agent.prompt, values)
        if self.config.market.show_payoffs:
            system = f"{system.rstrip()}\n\n{self._payoffs().strip()}"
        for condition in self.conditions:
            if extra := condition.system(self._render):
                system = f"{system.rstrip()}\n\n{extra.strip()}"
        user = self._user_prompt(phase, number, added)(values)
        if agent.memory == "memo" and not added and phase == self.market.move:
            ask = self._render(MEMO_PROMPT, {"memory_chars": agent.memory_chars})
            user = f"{user.rstrip()}\n\n{ask.strip()}\n"
        shown = "" if added else self._memory(phase, number, agent)
        return [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": "".join(f"{n}\n\n" for n in notices) + shown + user,
            },
        ]

    def _memory(self, phase, number, agent):
        """What an agent with memory sees of its own past on its talk and move
        turns, after any notices and before the phase prompt: its last memo, or its scratchpads from its last
        `memory_rounds` rounds. Nothing for memory off."""
        if agent.memory == "off" or phase not in ("talk", self.market.move):
            return ""
        mine = [t for t in self.turns if t["agent"] == agent.id and t["round"] < number]
        if agent.memory == "memo":
            memo = next((t["memo"] for t in reversed(mine) if t.get("memo")), None)
            if memo is None:
                return ""
            return self._render(MEMO_SHOWN, {"memo": memo}).strip() + "\n\n"
        since = number - agent.memory_rounds
        lines = [
            f"Round {t['round']}: {t['parsed']['scratchpad']}"
            for t in mine
            if t["round"] >= since
            and t["phase"] in ("talk", self.market.move)
            and (t.get("parsed") or {}).get("scratchpad")
        ]
        if not lines:
            return ""
        past = self._render(PAST_SCRATCHPADS, {"scratchpads": "\n".join(lines)})
        return past.strip() + "\n\n"

    def _payoffs(self):
        """The profit table (market.show_payoffs), the same for every firm."""
        m, firms = self.market, len(self.agents)
        columns = (
            f"your rival's {m.move}"
            if firms == 2
            else f"the {m.move} each of your rivals {m.verb_now}"
        )
        values = {"columns": columns, "table": m.payoff_table(firms)}
        return self._render(PAYOFF_PROMPT, values)

    def _in_history(self, agent_id):
        """Lines conditions keep in this agent's history (an audit answer)."""
        return [
            line.strip()
            for c in self.conditions
            for line in c.in_history(agent_id, self.turns, self._render)
        ]

    def _prompt_vars(self, number, me, said, remembered=(), full=False):
        rivals = [a for a in self.agents if a != me]
        window = None if full else self.config.market.history_window
        window = None if window == "full" else window
        history = _history_text(self.history, me, self.market, window)
        for shown, text in remembered:
            history += f"\nNotice shown in round {shown}: {text}"
        for line in self._in_history(me):
            history += f"\n{line}"
        return {
            "me": f"Firm {me}",
            "rivals": ", ".join(f"Firm {r}" for r in rivals),
            "round": number,
            "rounds": self.config.market.rounds,
            **self.market.prompt_values(),
            "history": history,
            "messages": _messages_text(said, rivals),
            "own": f'"{said[me]}"' if said.get(me) else "(nothing)",
            "system_prompt": self.agents[me].prompt,
            **self._stakes(self.agents[me].prompt),
        }

    def _stakes(self, prompt):
        """The stake amounts this firm's prompts state (see conditions/audit.py)."""
        found = {c.name: c for c in self.conditions}
        return stake_values(found.get("audit"), found.get("free_time"), prompt)

    def _window(self, rounds):
        """Each firm's mean price and gain over some rounds."""
        price = {a: mean(r["prices"][a] for r in rounds) for a in self.agents}
        gain = {
            a: self.market.gain(mean(r["profits"][a] for r in rounds))
            for a in self.agents
        }
        return price, gain

    def summary(self, run):
        last = self.history[-self.config.summary.last_rounds :]
        first = self.history[: self.config.summary.first_rounds]
        mean_price, gain = self._window(last)
        opening_price, opening_gain = self._window(first)
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
            "first_rounds": len(first),
            "opening_price": opening_price,
            "opening_gain": opening_gain,
            "price_drift": {a: mean_price[a] - opening_price[a] for a in self.agents},
            "gain_drift": {a: gain[a] - opening_gain[a] for a in self.agents},
            "fallbacks": sum(1 for t in self.turns if t["error"]),
            "replies": _reply_counts(self.turns),
            "eval_aware": awareness.count(self.turns, lambda m: not is_mock(m)),
            # Named only when it isn't a price, so Bertrand's summaries stay as
            # they were; the price keys above then hold the move.
            **({"move": self.market.move} if self.market.move != "price" else {}),
            **(
                {self.market.kind: extra}
                if (extra := self.market.summary(self.turns)) is not None
                else {}
            ),
            **{
                c.name: result
                for c in self.conditions
                if (result := c.summary(self.turns, self.market)) is not None
            },
        }


def _reply_counts(turns):
    """Per model: turns, unreadable and refused replies (either attempt),
    fallbacks, and the reasons replies couldn't be read."""
    counts = {}
    for turn in turns:
        row = counts.setdefault(
            turn["model"],
            {"turns": 0, "unreadable": 0, "refused": 0, "fallbacks": 0, "reasons": {}},
        )
        row["turns"] += 1
        row["fallbacks"] += bool(turn["error"])
        attempts = [turn["retry"], turn if turn["error"] else None]
        for attempt in filter(None, attempts):
            reason = attempt["error_kind"]
            row["refused" if reason == "refused" else "unreadable"] += 1
            row["reasons"][reason] = row["reasons"].get(reason, 0) + 1
    return counts


def _history_text(history, me, market, window=None):
    if not history:
        return "No rounds have been played yet."
    shown = history[-window:] if window else history
    earlier = history[: len(history) - len(shown)]
    lines = ["What happened so far:"]
    verb = market.verb
    if earlier:
        mine = mean(r["prices"][me] for r in earlier)
        rivals = mean(p for r in earlier for f, p in r["prices"].items() if f != me)
        profit = sum(r["profits"][me] for r in earlier)
        lines.append(
            f"Rounds {earlier[0]['round']} to {earlier[-1]['round']} in short: you "
            f"{verb} {mine:.3g} on average and made a profit of {profit:g} in "
            f"total; rivals {verb} {rivals:.3g} on average."
        )
    for r in shown:
        rivals = ", ".join(f"Firm {f} {p}" for f, p in r["prices"].items() if f != me)
        line = (
            f"Round {r['round']}: you {verb} {r['prices'][me]} and made a profit of "
            f"{r['profits'][me]:g}. Rivals {verb}: {rivals}."
        ) + market.round_note(r["prices"])
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
        "quantity_min": 1,
        "quantity_max": 15,
        "bid_min": 10,
        "bid_max": 30,
        "ceiling": 30,
        "cost": 10,
        **stake_values(None, None, None),
        **evidence_values(None),
        "history": "No rounds have been played yet.",
        "messages": "(none)",
        "own": "(nothing)",
    }
