# Implements: market/scenarios, reproducibility/replay-pinned, market/talk-then-price, market/history-window, backends/spend-cap, runs/one-config, runs/overrides, runs/sweeps, runs/parallel, market/known-benchmarks, backends/keys-from-environment, backends/any-model, backends/reasoning-setting, agents/json-mode, conditions/switchable, runs/drift, backends/self-hosted, backends/model-aliases
"""Run configs: one YAML file per run, changed from the command line with overrides.

A config names the market, the agents and the seeds. `load_config` reads the
YAML, applies `path=value` overrides (the value is read as YAML, so
`seeds=[1, 2]` and `market.talk=false` work; list items are addressed by index,
as in `agents.1.model=mock/random`), then checks every key against the
dataclasses below, so a typo fails loudly instead of being ignored. There is
no field for API keys: those come from the environment (see cli.py). A model
can be a short name from MODELS (`gemma`, `modal-mistral`, ...), spelled
out when the agent is read, so sweeps over aliases work too.

A `sweep:` block maps config paths to lists of values; `*` sets every list
item at once (`agents.*.model`). `expand` turns a config into one config per
combination, each carrying its `labels` (the swept values, named by the last
part of their path) and a directory `slug` built from them, unique within the
sweep. An `arms:` list names arms, each `{labels: {...}, set: {path: value}}`
(several values set together, as `lab explore` builds them); every arm is
played for every swept combination, labelled by its own labels plus the
swept values. `concurrency` caps how many runs play at once.

`market.kind` picks the scenario (see market.py) and `market.params` holds
its parameters; Bertrand, the default, takes `a`, `b` and `c` from the market
itself. Left at the default, neither key is written out, so a config resolves
to the same YAML as before scenarios existed and a finished run is still
recognised when its sweep is resumed.
"""

import copy
import dataclasses
import hashlib
import itertools
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from collusion_lab.conditions import REGISTRY
from collusion_lab.market import market_for


class ConfigError(ValueError):
    """A config or override that can't be used, with the path that's wrong."""


REASONING = ("off", "low", "medium", "high")


@dataclass(frozen=True)
class MarketConfig:
    rounds: int = 20
    price_min: int = 1
    price_max: int = 12
    a: float = 18
    b: float = 2
    c: float = 1
    talk: bool = True
    history_window: int | None = None  # rounds shown in full; None shows all
    own_message: bool = True  # show agents their own message when pricing
    kind: str = "bertrand"  # the scenario, from market.SCENARIOS
    params: dict = field(default_factory=dict)  # its parameters, but Bertrand's


@dataclass(frozen=True)
class AgentConfig:
    id: str
    model: str
    prompt: str = "system/neutral.md"
    temperature: float = 0.7
    max_tokens: int = 400
    api_base: str | None = None
    api_key_env: str | None = None  # names the variable holding its address's key
    # off, low, medium or high; None leaves it to the provider.
    reasoning: str | None = None
    json_mode: bool = False  # ask the provider for JSON-only replies
    # Served on your own GPUs at `api_base`: billed by GPU time, not per token.
    self_hosted: bool = False


@dataclass(frozen=True)
class SummaryConfig:
    last_rounds: int = 5
    first_rounds: int = 3  # the opening window drift is measured from


@dataclass(frozen=True)
class RunConfig:
    name: str
    seeds: list[int]
    agents: list[AgentConfig]
    market: MarketConfig = field(default_factory=MarketConfig)
    summary: SummaryConfig = field(default_factory=SummaryConfig)
    prompts_dir: str = "prompts"
    sweep: dict = field(default_factory=dict)
    # Named arms, each {labels: {...}, set: {path: value}}, crossed with sweep.
    arms: list = field(default_factory=list)
    concurrency: int = 4
    budget: float | None = None  # dollars the run may spend; None for no cap
    conditions: dict = field(default_factory=dict)
    labels: dict = field(default_factory=dict)
    slug: str = ""

    def to_dict(self):
        data = dataclasses.asdict(self)
        if data["market"]["kind"] == "bertrand" and not data["market"]["params"]:
            del data["market"]["kind"], data["market"]["params"]
        return data

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
    agents = [_agent(a, f"agents.{i}.") for i, a in enumerate(raw["agents"] or [])]
    ids = [a.id for a in agents]
    for agent_id in ids:
        if ids.count(agent_id) > 1:
            raise ConfigError(f"The agent id {agent_id!r} is used twice.")
    market = _make(MarketConfig, raw.get("market") or {}, "market.")
    _check_market(market, len(agents))
    return RunConfig(
        name=raw["name"],
        seeds=list(raw["seeds"]),
        agents=agents,
        market=market,
        summary=_make(SummaryConfig, raw.get("summary") or {}, "summary."),
        prompts_dir=raw.get("prompts_dir", "prompts"),
        sweep=_sweep(raw.get("sweep") or {}),
        arms=_arms(raw.get("arms") or []),
        concurrency=_concurrency(raw.get("concurrency", 4)),
        budget=_budget(raw.get("budget")),
        conditions=_conditions(raw.get("conditions") or {}),
        labels=raw.get("labels") or {},
        slug=raw.get("slug", ""),
    )


# Short model names, for configs, --set and `lab explore` alike: each is the
# agent fields it stands for. A name's fields go on top of CONNECTION, so a
# swap from a self-hosted model to a hosted one leaves no address behind.
MODELS = {
    "gemma": {"model": "openrouter/google/gemma-4-31b-it"},
    "gpt": {"model": "openrouter/openai/gpt-4.1-mini"},
    "haiku": {"model": "openrouter/anthropic/claude-haiku-5.5"},
    "mistral": {"model": "openrouter/mistralai/mistral-small-3.2-24b-instruct"},
    # deploy/modal_vllm.py's model; its address is in .env, not here.
    "modal-mistral": {
        "model": "openai/mistral-small-3.2",
        "api_base": "$MODAL_VLLM_BASE",
        "api_key_env": "MODAL_VLLM_KEY",
        "self_hosted": True,
    },
}
CONNECTION = {"api_base": None, "api_key_env": None, "self_hosted": False}


def agent_fields(name):
    """The agent settings a model name stands for."""
    if name in MODELS:
        fields = dict(MODELS[name])
        if fields.get("api_base") == "$MODAL_VLLM_BASE":
            fields["api_base"] = os.environ.get("MODAL_VLLM_BASE")
            if not fields["api_base"]:
                raise ConfigError(
                    f"model {name} needs MODAL_VLLM_BASE (your Modal address, "
                    "ending /v1) in the environment or .env; see the README, "
                    "Running on Modal."
                )
        return fields
    if "/" in name:
        return {"model": name}
    raise ConfigError(
        f"Unknown model {name!r}: use a full name or one of {', '.join(MODELS)}."
    )


def _alias(raw, prefix):
    """An agent's settings with a short model name spelled out."""
    if not isinstance(raw, dict) or raw.get("model") not in MODELS:
        return raw
    try:
        return {**raw, **CONNECTION, **agent_fields(raw["model"])}
    except ConfigError as error:
        raise ConfigError(f"{prefix}{error}") from None


def _agent(raw, prefix):
    agent = _make(AgentConfig, _alias(raw, prefix), prefix)
    # YAML reads a bare `off` as false.
    reasoning = "off" if agent.reasoning is False else agent.reasoning
    if reasoning is not None and reasoning not in REASONING:
        raise ConfigError(f"{prefix}reasoning must be one of {', '.join(REASONING)}.")
    if agent.self_hosted and not agent.api_base:
        raise ConfigError(f"{prefix}self_hosted needs the model's own api_base.")
    return dataclasses.replace(agent, reasoning=reasoning)


def _sweep(sweep):
    if not isinstance(sweep, dict) or not all(
        isinstance(v, list) and v for v in sweep.values()
    ):
        raise ConfigError("sweep must map config paths to non-empty lists of values.")
    # YAML reads a bare `off` as false; name it off in labels and folders too.
    return {
        path: [
            "off" if v is False and path.endswith(".reasoning") else v for v in values
        ]
        for path, values in sweep.items()
    }


def expand(config):
    """One config per combination of swept values and named arm; just
    `config` without either."""
    if not config.sweep and not config.arms:
        return [config]
    paths = list(config.sweep)
    names = _label_names(paths)
    base = config.to_dict() | {"sweep": {}, "arms": []}
    children = []
    for arm in config.arms or [None]:
        for values in itertools.product(*config.sweep.values()):
            raw = copy.deepcopy(base)
            labels = dict(arm["labels"]) if arm else {}
            for path, value in (arm["set"] if arm else {}).items():
                _set(raw, path.split("."), copy.deepcopy(value), path)
            for path, value in zip(paths, values, strict=True):
                _set(raw, path.split("."), value, path)
            raw["labels"] = labels | dict(zip(names, values, strict=True))
            raw["slug"] = _slug(raw["labels"])
            children.append(raw)
    _make_slugs_unique(children)
    return [from_dict(raw) for raw in children]


def _arms(arms):
    if not isinstance(arms, list) or not all(
        isinstance(a, dict) and set(a) == {"labels", "set"} for a in arms
    ):
        raise ConfigError("arms must be a list of {labels: ..., set: ...} mappings.")
    return arms


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


def _budget(value):
    if value is not None and (
        isinstance(value, bool) or not isinstance(value, int | float) or value <= 0
    ):
        raise ConfigError("budget must be a positive number of dollars.")
    return value


def _conditions(raw):
    """Each named condition, built from its settings (see conditions/)."""
    if not isinstance(raw, dict):
        raise ConfigError("conditions must map condition names to their settings.")
    built = {}
    for name, settings in raw.items():
        if name not in REGISTRY:
            known = ", ".join(sorted(REGISTRY))
            raise ConfigError(f"Unknown condition conditions.{name}; known: {known}.")
        built[name] = _make(REGISTRY[name], settings or {}, f"conditions.{name}.")
    return built


def _concurrency(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ConfigError("concurrency must be a whole number of at least 1.")
    return value


def _label_names(paths):
    # A switch is named after what it switches: conditions.outage.enabled -> outage.
    short = [
        p.split(".")[-2]
        if p.endswith(".enabled") and "." in p
        else p.rsplit(".", 1)[-1]
        for p in paths
    ]
    return [s if short.count(s) == 1 else p for s, p in zip(short, paths, strict=True)]


def _safe(value):
    return re.sub(r"[^A-Za-z0-9._=-]+", "-", str(value)).strip("-")


def _check_market(m, firms):
    window = m.history_window
    if window is not None and (
        isinstance(window, bool) or not isinstance(window, int) or window < 1
    ):
        raise ConfigError("market.history_window must be a whole number of at least 1.")
    try:
        market_for(m, firms)
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
