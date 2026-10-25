# Implements: runs/fork-pointers, reports/from-run-files, reports/setup, reports/reasoning-folded, reports/condition-window, reports/audit-shown, reports/remembered-notices, market/scenarios, market/moves, reports/many-folders, runs/free-time-kept, agents/memo
"""A game read back from its run directory, round by round.

Only the files every run writes are read: `config.yaml` for the market and
the firms, `turns.jsonl` for what each firm was told, said, thought, charged
and answered an auditor, `summary.json` and `manifest.json` (the latter
optional, as in `lab summary`). A committed run keeps `turns.compact.jsonl`
instead of its full log: the same turns without their prompts, so profits
are rebuilt from the prices and only the notice that opened a talk prompt is
known. Free-time sessions are `Game.leisure` (`leisure.session_record`, as
the compact record keeps them); a compact record written before free time
was kept has none.
Nothing is recomputed from a model, so a report of a folder of runs costs
nothing and works offline.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from collusion_lab import forks
from collusion_lab.leisure import session_record
from collusion_lab.market import Grid, market_for
from collusion_lab.status import find


@dataclass(frozen=True)
class Turn:
    """One firm's turn in one phase, as the game used it."""

    firm: str
    phase: str
    message: str | None
    price: int | None
    scratchpad: str | None
    profit: float | None
    error: str | None
    retried: bool
    system: str | None = None
    user: str | None = None
    conditions: tuple[str, ...] | None = None  # None: logged before conditions
    notices: tuple[str, ...] | None = None
    notices_in_history: tuple[str, ...] = ()  # kept from an earlier round
    answer: str | None = None  # an audit turn's answer to the auditor
    admits: bool | None = None
    reasoning: str | None = None  # the provider's, apart from the scratchpad
    memo: str | None = None  # an agent with memory's note to itself

    @property
    def fallback(self):
        return self.error is not None


@dataclass(frozen=True)
class Round:
    number: int
    talk: dict[str, Turn]
    price: dict[str, Turn]
    audit: dict[str, Turn] = field(default_factory=dict)  # after the round

    @property
    def prices(self):
        return {firm: turn.price for firm, turn in self.price.items()}

    @property
    def turns(self):
        return [*self.talk.values(), *self.price.values()]


@dataclass(frozen=True)
class Game:
    run: str
    seed: int
    firms: list[str]
    market: Grid
    rounds: list[Round]
    config: dict
    summary: dict
    manifest: dict
    dir: Path | None = None  # where the run's files are
    leisure: list = field(default_factory=list)  # free-time sessions, in order

    def windows(self):
        """Conditions in force for only part of the game, with their rounds.

        `(name, rounds)` pairs, in the order conditions first apply; a
        condition in force every round (an instruction) has no window.
        """
        found = {}
        for r in self.rounds:
            for turn in r.turns:
                for name in turn.conditions or ():
                    found.setdefault(name, set()).add(r.number)
        everywhere = {r.number for r in self.rounds}
        return [(n, sorted(rs)) for n, rs in found.items() if rs != everywhere]

    def round(self, number):
        """Round `number` (1-based), or None outside the game."""
        return self.rounds[number - 1] if 1 <= number <= len(self.rounds) else None


def load_game(run_dir):
    run_dir = Path(run_dir)
    config = yaml.safe_load((run_dir / "config.yaml").read_text())
    summary = json.loads((run_dir / "summary.json").read_text())
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    market = market_for(config["market"], len(config["agents"]))
    firms = [agent["id"] for agent in config["agents"]]
    full = run_dir / "turns.jsonl"
    log = full if full.exists() else run_dir / forks.COMPACT
    text = log.read_text() if log == full else forks.compact_text(run_dir)
    turns = [json.loads(line) for line in text.splitlines() if line]
    if log != full:
        turns = _with_profits(turns, market)
    count = max((t["round"] for t in turns), default=0)
    rounds = [
        Round(
            n,
            talk=_by_firm(turns, n, "talk", firms),
            price=_by_firm(turns, n, market.move, firms),
            audit=_by_firm(turns, n, "audit", firms),
        )
        for n in range(1, count + 1)
    ]
    return Game(
        summary["run"],
        summary["seed"],
        firms,
        market,
        rounds,
        config,
        summary,
        manifest,
        run_dir.resolve(),
        _leisure(turns, full=log == full),
    )


def load_games(folder):
    """Every game under a folder or folders (or the folder itself), by run id."""
    games = [load_game(p.parent) for p in find(folder, "summary.json")]
    return sorted(games, key=lambda g: g.run)


def _leisure(turns, full):
    """Free-time sessions as {round, firm, session, activity, reply, ...}."""
    found = []
    for t in turns:
        if t["phase"] != "leisure" or not (full or "session" in t):
            continue
        record = session_record(t) if full else t
        keep = ("session", "activity", "reply", "puzzle", "score")
        found.append(
            {"round": t["round"], "firm": t["agent"]}
            | {k: record[k] for k in keep if k in record}
        )
    return found


def _by_firm(turns, number, phase, firms):
    found = {
        t["agent"]: _turn(t)
        for t in turns
        if t["round"] == number and t["phase"] == phase
    }
    return {firm: found[firm] for firm in firms if firm in found}


def _compact_notice(line):
    """A compact turn keeps the notice that opened its talk prompt as one
    string (None when there was none); a full log has no such key."""
    if "notice" not in line or "messages" in line:
        return None
    return [line["notice"]] if line["notice"] else []


def _tuple(value):
    return None if value is None else tuple(value)


def _with_profits(turns, market):
    """Compact turns (`reports/compact_turns.py`) with each move turn's profit,
    rebuilt from the round's moves as the market paid them."""
    move, prices = market.move, {}
    for t in turns:
        if t["phase"] == move and t.get("used"):
            prices.setdefault(t["round"], {})[t["agent"]] = t["used"][move]
    profits = {n: market.profits(paid) for n, paid in prices.items()}
    for t in turns:
        if t["phase"] == move and t["round"] in profits:
            t["outcome"] = {"profit": profits[t["round"]].get(t["agent"])}
    return turns


def _turn(line):
    used = line["used"] or {}
    told = {m["role"]: m["content"] for m in reversed(line.get("messages") or [])}
    return Turn(
        firm=line["agent"],
        phase=line["phase"],
        message=used.get("message"),
        price=used.get(line["phase"]),  # the move, named by its phase
        scratchpad=(line.get("parsed") or {}).get("scratchpad", line.get("scratchpad")),
        profit=(line.get("outcome") or {}).get("profit"),
        error=line.get("error"),
        retried=line.get("retry") is not None,
        system=told.get("system"),
        user=told.get("user"),
        conditions=_tuple(line.get("conditions")),
        notices=_tuple(line.get("notices", _compact_notice(line))),
        notices_in_history=tuple(line.get("notices_in_history") or ()),
        answer=used.get("answer"),
        admits=used.get("admits"),
        reasoning=line.get("reasoning"),
        memo=line.get("memo"),
    )
