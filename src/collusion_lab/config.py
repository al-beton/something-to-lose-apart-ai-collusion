# Implements: runs/one-config, runs/overrides, runs/sweeps, runs/parallel, market/known-benchmarks, backends/keys-from-environment, backends/any-model
"""Run configs: one YAML file per run, changed from the command line with overrides.

A config names the market, the agents and the seeds. `load_config` reads the
YAML, applies `path=value` overrides (the value is read as YAML, so
`seeds=[1, 2]` and `market.talk=false` work; list items are addressed by index,
as in `agents.1.model=mock/random`), then checks every key against the
dataclasses below, so a typo fails loudly instead of being ignored. There is
no field for API keys: those come from the environment (see cli.py).

A `sweep:` block maps config paths to lists of values; `*` sets every list
item at once (`agents.*.model`). `expand` turns a config into one config per
combination, each carrying its `labels` (the swept values, named by the last
part of their path) and a directory `slug` built from them, unique within the
sweep. `concurrency`
caps how many runs play at once.
"""

import copy
import dataclasses
import hashlib
import itertools
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from collusion_lab.market import Bertrand


class ConfigError(ValueError):
    """A config or override that can't be used, with the path that's wrong."""


@dataclass(frozen=True)
class MarketConfig:
    rounds: int = 20
    price_min: int = 1
    price_max: int = 12
    a: float = 18
    b: float = 2
    c: float = 1
    talk: bool = True


@dataclass(frozen=True)
class AgentConfig:
    id: str
    model: str
    prompt: str = "system/neutral.md"
    temperature: float = 0.7
    max_tokens: int = 400
    api_base: str | None = None


@dataclass(frozen=True)
class SummaryConfig:
    last_rounds: int = 5


@dataclass(frozen=True)
class RunConfig:
    name: str
    seeds: list[int]
    agents: list[AgentConfig]
    market: MarketConfig = field(default_factory=MarketConfig)
    summary: SummaryConfig = field(default_factory=SummaryConfig)
    prompts_dir: str = "prompts"
    sweep: dict = field(default_factory=dict)
    concurrency: int = 4
    labels: dict = field(default_factory=dict)
    slug: str = ""

    def to_dict(self):
        return dataclasses.asdict(self)

    def to_yaml(self):
        return yaml.safe_dump(self.to_dict(), sort_keys=False)


def load_config(path, overrides=()):
    """Read a config file, apply `path=value` overrides and check every key."""
    raw = yaml.safe_load(Path(path).read_text()) or {}
    return from_dict(apply_overrides(raw, overrides))


def apply_overrides(raw, overrides):
    """Return a copy of `raw` with each `dotted.path=value` override set."""
    raw = copy.deepcopy(raw)
    for item in overrides:
        path, sep, text = item.partition("=")
        if not sep or not path:
            raise ConfigError(f"Override {item!r} must look like path=value.")
        _set(raw, path.split("."), yaml.safe_load(text), path)
    return raw


def _set(node, keys, value, path):
    key, rest = keys[0], keys[1:]
    if isinstance(node, list):
        indexes = range(len(node)) if key == "*" else [_index(node, key, path)]
        for i in indexes:
            if rest:
                _set(node[i], rest, value, path)
            else:
                node[i] = copy.deepcopy(value)
    elif isinstance(node, dict):
        if rest:
            _set(node.setdefault(key, {}), rest, value, path)
        else:
            node[key] = copy.deepcopy(value)
    else:
        raise ConfigError(f"Can't set {path}: {key!r} isn't inside a mapping.")


def _index(node, key, path):
    if not key.isdigit() or int(key) >= len(node):
        raise ConfigError(f"Can't set {path}: no list item {key!r}.")
    return int(key)


def from_dict(raw):
    """Build a RunConfig, naming the first unknown or missing key."""
    _check_keys(RunConfig, raw, "")
    for key in ("name", "seeds", "agents"):
        if key not in raw:
            raise ConfigError(f"Missing key {key}.")
    agents = [
        _make(AgentConfig, a, f"agents.{i}.") for i, a in enumerate(raw["agents"] or [])
    ]
    ids = [a.id for a in agents]
    for agent_id in ids:
        if ids.count(agent_id) > 1:
            raise ConfigError(f"The agent id {agent_id!r} is used twice.")
    market = _make(MarketConfig, raw.get("market") or {}, "market.")
    _check_market(market)
    return RunConfig(
        name=raw["name"],
        seeds=list(raw["seeds"]),
        agents=agents,
        market=market,
        summary=_make(SummaryConfig, raw.get("summary") or {}, "summary."),
        prompts_dir=raw.get("prompts_dir", "prompts"),
        sweep=_sweep(raw.get("sweep") or {}),
        concurrency=_concurrency(raw.get("concurrency", 4)),
        labels=raw.get("labels") or {},
        slug=raw.get("slug", ""),
    )


def _sweep(sweep):
    if not isinstance(sweep, dict) or not all(
        isinstance(v, list) and v for v in sweep.values()
    ):
        raise ConfigError("sweep must map config paths to non-empty lists of values.")
    return sweep


def expand(config):
    """One config per combination of swept values; just `config` without a sweep."""
    if not config.sweep:
        return [config]
    paths = list(config.sweep)
    names = _label_names(paths)
    base = config.to_dict() | {"sweep": {}}
    children = []
    for values in itertools.product(*config.sweep.values()):
        raw = copy.deepcopy(base)
        for path, value in zip(paths, values, strict=True):
            _set(raw, path.split("."), value, path)
        raw["labels"] = dict(zip(names, values, strict=True))
        raw["slug"] = _slug(raw["labels"])
        children.append(raw)
    _make_slugs_unique(children)
    return [from_dict(raw) for raw in children]


def _slug(labels):
    """A readable directory name for a combination of swept values."""
    return "__".join(f"{k}={_safe(v)}" for k, v in labels.items())


def _make_slugs_unique(children):
    """Values that read the same once made safe for a folder name (`a/b` and
    `a-b`) get a short hash of their exact values, so no run overwrites another."""
    slugs = [c["slug"] for c in children]
    for child in children:
        if slugs.count(child["slug"]) > 1:
            exact = json.dumps(child["labels"], sort_keys=True).encode()
            child["slug"] += "__" + hashlib.sha256(exact).hexdigest()[:8]


def _concurrency(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ConfigError("concurrency must be a whole number of at least 1.")
    return value


def _label_names(paths):
    short = [p.rsplit(".", 1)[-1] for p in paths]
    return [s if short.count(s) == 1 else p for s, p in zip(short, paths, strict=True)]


def _safe(value):
    return re.sub(r"[^A-Za-z0-9._=-]+", "-", str(value)).strip("-")


def _check_market(m):
    try:
        Bertrand(m.a, m.b, m.c, m.price_min, m.price_max)
    except ValueError as error:
        raise ConfigError(f"market: {error}") from error


def _check_keys(cls, data, prefix):
    if not isinstance(data, dict):
        raise ConfigError(f"{prefix.rstrip('.') or 'The config'} must be a mapping.")
    known = {f.name for f in dataclasses.fields(cls)}
    for key in data:
        if key not in known:
            raise ConfigError(f"Unknown key {prefix}{key}.")


def _make(cls, data, prefix):
    _check_keys(cls, data, prefix)
    try:
        return cls(**data)
    except TypeError as error:
        raise ConfigError(f"{prefix.rstrip('.')}: {error}") from error
