# Implements: runs/one-config, runs/overrides, market/known-benchmarks, backends/keys-from-environment, backends/any-model
"""Run configs: one YAML file per run, changed from the command line with overrides.

A config names the market, the agents and the seeds. `load_config` reads the
YAML, applies `path=value` overrides (the value is read as YAML, so
`seeds=[1, 2]` and `market.talk=false` work; list items are addressed by index,
as in `agents.1.model=mock/random`), then checks every key against the
dataclasses below, so a typo fails loudly instead of being ignored. There is
no field for API keys: those come from the environment (see cli.py).
"""

import copy
import dataclasses
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
    for key in keys[:-1]:
        node = _child(node, key, path)
    last = keys[-1]
    if isinstance(node, list):
        node[_index(node, last, path)] = value
    elif isinstance(node, dict):
        node[last] = value
    else:
        raise ConfigError(f"Can't set {path}: {last!r} isn't inside a mapping.")


def _child(node, key, path):
    if isinstance(node, list):
        return node[_index(node, key, path)]
    if isinstance(node, dict):
        return node.setdefault(key, {})
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
    )


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
