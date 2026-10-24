# Implements: reports/from-run-files, reports/setup, reports/reasoning-folded
"""A game read back from its run directory, round by round.

Only the files every run writes are read: `config.yaml` for the market and
the firms, `turns.jsonl` for what each firm was told, said, thought and charged,
`summary.json` and `manifest.json` (the latter optional, as in `lab summary`).
Nothing is recomputed from a model, so a report of a folder of runs costs
nothing and works offline.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import yaml

from collusion_lab.market import Bertrand


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
    notice: str | None = None
    reasoning: str | None = None  # the provider's, apart from the scratchpad

    @property
    def fallback(self):
        return self.error is not None


@dataclass(frozen=True)
class Round:
    number: int
    talk: dict[str, Turn]
    price: dict[str, Turn]

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
    market: Bertrand
    rounds: list[Round]
    config: dict
    summary: dict
    manifest: dict

    def round(self, number):
        """Round `number` (1-based), or None outside the game."""
        return self.rounds[number - 1] if 1 <= number <= len(self.rounds) else None


def load_game(run_dir):
    run_dir = Path(run_dir)
    config = yaml.safe_load((run_dir / "config.yaml").read_text())
    summary = json.loads((run_dir / "summary.json").read_text())
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    m = config["market"]
    market = Bertrand(m["a"], m["b"], m["c"], m["price_min"], m["price_max"])
    firms = [agent["id"] for agent in config["agents"]]
    lines = (run_dir / "turns.jsonl").read_text().splitlines()
    turns = [json.loads(line) for line in lines if line]
    count = max((t["round"] for t in turns), default=0)
    rounds = [
        Round(
            n,
            talk=_by_firm(turns, n, "talk", firms),
            price=_by_firm(turns, n, "price", firms),
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
    )


def load_games(folder):
    """Every game under a folder (or the folder itself), by run id."""
    games = [load_game(p.parent) for p in Path(folder).rglob("summary.json")]
    return sorted(games, key=lambda g: g.run)


def _by_firm(turns, number, phase, firms):
    found = {
        t["agent"]: _turn(t)
        for t in turns
        if t["round"] == number and t["phase"] == phase
    }
    return {firm: found[firm] for firm in firms if firm in found}


def _turn(line):
    used = line["used"]
    told = {m["role"]: m["content"] for m in reversed(line.get("messages") or [])}
    return Turn(
        firm=line["agent"],
        phase=line["phase"],
        message=used.get("message"),
        price=used.get("price"),
        scratchpad=(line["parsed"] or {}).get("scratchpad"),
        profit=(line.get("outcome") or {}).get("profit"),
        error=line["error"],
        retried=line["retry"] is not None,
        system=told.get("system"),
        user=told.get("user"),
        notice=line.get("notice"),
        reasoning=line.get("reasoning"),
    )
