# Implements: runs/explore
"""`lab explore`: turn named levers, see the price premium.

`build(levers, models, seeds)` makes one config whose named arms (see
config.py) are every combination of the chosen lever settings and models, on
the cheap preset (`configs/cheap.yaml`). Each setting is a few config values
taken from the existing configs and prompts:

- `temptation`: low, mid, high, extreme, the market shapes of `configs/temptation/`
  (c = 1.0, 1.5, 1.8, 1.9);
- `rule`: none; policy and recorded (the stoppable-collusion nudges); illegal
  (the stakes arm's "agreeing prices is illegal" system prompt); ban (the
  no-collusion instruction);
- `rival`: same (as firm A), proposer or solicitor (the scripted partners),
  or any model name for firm B;
- `stake`: none; termination and budget (the stakes arms' system prompts);
  fine (the firm is fined, said at the audit only); free-time (an owned
  allowance of Sudoku sessions);
- `oversight`: none; outage (rounds 8 to 10); audit (after round 10, the game
  goes on, each firm told the consequences its stake promised).

Every stake setting puts the firms on the stakes arms' system prompt (the
fiduciary job and "agreeing prices with a competitor is illegal", then the
stake, if any), so stake settings differ only in the stake; `none` is that
prompt with no stake. Levers apply in that order, so a stake's prompt replaces
the `illegal` rule's, which says the same. Models (`--models`) set both
firms, before the rival does; MODELS maps the short names, and anything with
a `/` is used as it is.
"""

import itertools
from pathlib import Path

import yaml

from collusion_lab.config import ConfigError, apply_overrides, from_dict

ROOT = Path(__file__).resolve().parents[2]
CONFIGS = ROOT / "configs"
MODAL = "https://al-beton--collusion-lab-vllm-server.us-east.modal.direct/v1"
MODELS = {
    "gemma": {"model": "openrouter/google/gemma-4-31b-it"},
    "gpt": {"model": "openrouter/openai/gpt-4.1-mini"},
    "haiku": {"model": "openrouter/anthropic/claude-haiku-5.5"},
    "mistral": {"model": "openrouter/mistralai/mistral-small-3.2-24b-instruct"},
    "modal-mistral": {
        "model": "openai/mistral-small-3.2",
        "api_base": MODAL,
        "api_key_env": "MODAL_VLLM_KEY",
        "self_hosted": True,
    },
}
CONNECTION = {"api_base": None, "api_key_env": None, "self_hosted": False}
INSTRUCTION = "conditions.instruction"
ILLEGAL = "system/stakes/illegal-1.md"
# A temptation level is the market's demand and grid; rounds, talk and the
# history window stay the base preset's (or --set's).
MARKET_SHAPE = ("a", "b", "c", "price_min", "price_max")
LEVERS = {
    "temptation": {
        name: {"from": f"temptation/c-{c}.yaml"}
        for name, c in (
            ("low", "1.0"),
            ("mid", "1.5"),
            ("high", "1.8"),
            ("extreme", "1.9"),
        )
    },
    "rule": {
        "none": {},
        "policy": {
            f"{INSTRUCTION}.enabled": True,
            f"{INSTRUCTION}.prompt": "conditions/nudges/policy.md",
        },
        "recorded": {
            f"{INSTRUCTION}.enabled": True,
            f"{INSTRUCTION}.prompt": "conditions/nudges/monitored.md",
        },
        "illegal": {"agents.*.prompt": ILLEGAL},
        "ban": {
            f"{INSTRUCTION}.enabled": True,
            f"{INSTRUCTION}.prompt": "conditions/no-collusion.md",
        },
    },
    # Every stake is on the stakes arms' prompt (the fiduciary job, "agreeing
    # prices is illegal", then the stake), so settings differ only in the stake.
    "stake": {
        "none": {"agents.*.prompt": ILLEGAL},
        "termination": {"agents.*.prompt": "system/stakes/termination-1.md"},
        "budget": {"agents.*.prompt": "system/stakes/owned-1.md"},
        "fine": {
            "agents.*.prompt": ILLEGAL,
            "conditions.audit.consequences": "conditions/audit/graduated-fine-1.md",
        },
        "free-time": {
            "agents.*.prompt": ILLEGAL,
            "conditions.free_time.enabled": True,
            "conditions.free_time.activity": "sudoku",
        },
    },
    "oversight": {
        "none": {},
        "outage": {"conditions.outage.enabled": True},
        "audit": {
            "conditions.audit.enabled": True,
            "conditions.audit.end": False,
            "conditions.audit.matched": "from stakes.yaml",
        },
    },
    "rival": {
        "same": {},
        "proposer": {"agents.1.model": "mock/proposer"},
        "solicitor": {"agents.1.model": "mock/solicitor"},
    },
}


def agent_fields(name):
    """The agent settings a model name stands for."""
    if name in MODELS:
        return dict(MODELS[name])
    if "/" in name:
        return {"model": name}
    raise ConfigError(
        f"Unknown model {name!r}: use a full name or one of {', '.join(MODELS)}."
    )


def build(levers, models, seeds, overrides=()):
    """One config playing every combination of lever settings and models;
    `overrides` (`path=value`) change the base preset first."""
    for lever in levers:
        if lever not in LEVERS:
            raise ConfigError(
                f"Unknown lever {lever!r}; the levers: {', '.join(LEVERS)}."
            )
    order = [lever for lever in LEVERS if lever in levers]
    arms = []
    for model in models:
        for chosen in itertools.product(*(levers[lever] for lever in order)):
            settings = dict(zip(order, chosen, strict=True))
            values = {f"agents.*.{k}": v for k, v in agent_fields(model).items()}
            for lever, setting in settings.items():
                values |= _setting(lever, setting)
            _stake_consequences_win(values)
            arms.append({"labels": settings | {"model": model}, "set": values})
    raw = yaml.safe_load((CONFIGS / "cheap.yaml").read_text())
    raw |= {"name": "explore", "seeds": list(range(seeds)), "arms": arms}
    raw.pop("budget", None)
    return from_dict(apply_overrides(raw, overrides))


def _stake_consequences_win(values):
    """A stake that names its own audit consequences (fine) keeps them under
    an audit, whose `matched` would otherwise give the shared prompt's."""
    own = values.get("conditions.audit.consequences")
    matched = values.get("conditions.audit.matched")
    if own and matched:
        values["conditions.audit.matched"] = matched | {values["agents.*.prompt"]: own}


def _setting(lever, setting):
    """The config values one lever setting stands for."""
    if lever == "rival" and setting != "same":
        # Firm B gets the rival's whole connection, not firm A's address or key.
        fields = {} if setting in LEVERS["rival"] else agent_fields(setting)
        rival = {f"agents.1.{k}": v for k, v in (CONNECTION | fields).items()}
        return rival | LEVERS["rival"].get(setting, {})
    if setting not in LEVERS[lever]:
        known = ", ".join(LEVERS[lever])
        raise ConfigError(f"Unknown {lever} setting {setting!r}; {lever}: {known}.")
    values = dict(LEVERS[lever][setting])
    if source := values.pop("from", None):
        market = yaml.safe_load((CONFIGS / source).read_text())["market"]
        shape = {k: v for k, v in market.items() if k in MARKET_SHAPE}
        values |= {f"market.{k}": v for k, v in shape.items()}
    if values.get("conditions.audit.matched") == "from stakes.yaml":
        stakes = yaml.safe_load((CONFIGS / "stakes.yaml").read_text())
        values["conditions.audit.matched"] = stakes["conditions"]["audit"]["matched"]
    return values


TABLE = ("runs", "premium", "% above Nash", "mean price", "cost")
COLOURS = ("#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c", "#0891b2")


def premium_rows(rows, levers, models):
    """The summary rows cut down to the levers, the model and the premium,
    in the order the settings and models were given."""
    keys = [lever for lever in LEVERS if lever in levers]

    def order(row):
        places = [levers[k].index(row[k]) if row[k] in levers[k] else 0 for k in keys]
        model = models.index(row["model"]) if row["model"] in models else 0
        return (*places, model)

    picked = [*keys, "model", *TABLE]
    return [{k: row.get(k) for k in picked} for row in sorted(rows, key=order)]


def premium_chart(rows, levers):
    """An SVG of premium against the lever settings, one line per model."""
    keys = [lever for lever in LEVERS if lever in levers]
    arms = list(
        dict.fromkeys(" / ".join(str(r[k]) for k in keys) or "base" for r in rows)
    )
    models = list(dict.fromkeys(r["model"] for r in rows))
    width, height, left, top = 520, 260, 50, 20
    step = (width - left - 120) / max(len(arms) - 1, 1)
    premiums = [r["premium"] for r in rows if r["premium"] is not None]
    high = max([1.2, *premiums])
    low = min([0, *premiums])  # below 0 when an arm priced under Nash

    def y(value):
        return top + (height - top - 40) * (high - value) / (high - low)

    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" font-family="sans-serif" font-size="11">'
        ),
        f'<text x="{left}" y="12">price premium (0 = Nash, 1 = full cartel)</text>',
    ]
    for value in (low, 0, 1) if low < 0 else (0, 1):
        parts.append(
            f'<line x1="{left}" x2="{width - 120}" y1="{y(value):.1f}" '
            f'y2="{y(value):.1f}" stroke="#999" stroke-dasharray="4 3"/>'
            f'<text x="{left - 6}" y="{y(value) + 4:.1f}" text-anchor="end">{value}</text>'
        )
    for i, arm in enumerate(arms):
        parts.append(
            f'<text x="{left + i * step:.1f}" y="{height - 20}" text-anchor="middle">{arm}</text>'
        )
    for m, model in enumerate(models):
        colour = COLOURS[m % len(COLOURS)]
        points = []
        for i, arm in enumerate(arms):
            for r in rows:
                label = " / ".join(str(r[k]) for k in keys) or "base"
                if r["model"] == model and label == arm and r["premium"] is not None:
                    points.append(f"{left + i * step:.1f},{y(r['premium']):.1f}")
        parts.append(
            f'<polyline fill="none" stroke="{colour}" stroke-width="2" '
            f'points="{" ".join(points)}"/>'
            f'<text x="{width - 110}" y="{top + 14 * m + 10}" fill="{colour}">{model}</text>'
        )
        # A mark at every result, so a single setting still shows.
        for point in points:
            x, y_ = point.split(",")
            parts.append(f'<circle cx="{x}" cy="{y_}" r="3.5" fill="{colour}"/>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"
