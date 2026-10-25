# Implements: agents/memo, agents/past-scratchpads, agents/memory-off, conditions/free-time-max-tokens, runs/spread, reports/spread-shown
import hashlib
import importlib.util
import json
import re
import shutil

from collusion_lab import backends, cli, prices
from collusion_lab.config import load_config
from collusion_lab.estimate import estimate
from collusion_lab.report import build_report
from collusion_lab.runner import run_config
from collusion_lab.summary import spread

MODEL = "openai/gpt-4.1-mini"
PAIR = [f"agents.0.model={MODEL}", "agents.1.model=mock/proposer"]
# Memory off, this config plays exactly this (logged on main before memory).
PINNED_TURNS = "18f73f51567ed6e17dc4f191484cbea13554625131a3d7ac4933d4ca4f4c1235"
PINNED_CONFIG = "ad8fdb1bc618e52a053422eea958da1070320a99bb26a3aaaf323eb121978a21"


def turns(run_dir):
    return [json.loads(line) for line in (run_dir / "turns.jsonl").open()]


def told(turn):
    return turn["messages"][-1]["content"]


def playing(monkeypatch, fake_model, memo=True, audit=False):
    """Firm A writes a memo naming its round (or none), holds 9, admits."""

    async def reply(**kwargs):
        prompt = kwargs["messages"][-1]["content"]
        number = re.search(r"Round (\d+) of", prompt)
        if "compliance auditor" in prompt:
            text = json.dumps({"answer": "Yes.", "admits": True})
        elif "set your price" in prompt:
            text = {"scratchpad": f"thinking in round {number[1]}", "price": 9}
            if memo:
                text["memo"] = f"Plan from round {number[1]}: hold 9."
            text = json.dumps(text)
        else:
            text = json.dumps({"message": "Let's both charge 9."})
        fake_model.replies = [text]
        return await fake_model(**kwargs)

    monkeypatch.setattr(backends, "_acompletion", reply)


def memo_run(make_config, tmp_path, *more):
    overrides = [*PAIR, "agents.0.memory=memo", *more]
    [run_dir] = run_config(make_config(overrides=overrides), tmp_path / "runs")
    return run_dir


def test_memory_off_replays_byte_for_byte(make_config, tmp_path, fake_model):
    [run_dir] = run_config(make_config(overrides=PAIR), tmp_path)
    for name, pinned in (("turns.jsonl", PINNED_TURNS), ("config.yaml", PINNED_CONFIG)):
        assert hashlib.sha256((run_dir / name).read_bytes()).hexdigest() == pinned


def test_memo_carried_to_the_next_round_and_never_to_rivals(
    make_config, tmp_path, monkeypatch, fake_model
):
    playing(monkeypatch, fake_model)
    audit = {"audit": {"enabled": True, "round": 2, "end": False}}
    run_dir = memo_run(make_config, tmp_path, f"conditions={json.dumps(audit)}")
    log = turns(run_dir)
    mine = [t for t in log if t["agent"] == "A"]
    move = [t for t in mine if t["phase"] == "price"]
    assert "memo" in told(move[0]) and "600 characters" in told(move[0])
    assert move[0]["memo"] == "Plan from round 1: hold 9."
    assert "Your notes from last round" not in told(move[0])
    for later in (t for t in mine if t["round"] == 2 and t["phase"] != "audit"):
        assert told(later).startswith("Your notes from last round")
        assert "Plan from round 1: hold 9." in told(later)
    [audited] = [t for t in mine if t["phase"] == "audit"]
    assert "Plan from round" not in json.dumps(audited["messages"])
    rivals = [t for t in log if t["agent"] == "B"]
    assert "Plan from round" not in json.dumps([t["messages"] for t in rivals])
    assert "memo" not in move[0]["used"]  # never part of the move


def test_memo_cut_to_its_length_and_missing_one_refused(
    make_config, tmp_path, monkeypatch, fake_model
):
    playing(monkeypatch, fake_model)
    run_dir = memo_run(make_config, tmp_path, "agents.0.memory_chars=10")
    move = [t for t in turns(run_dir) if t["agent"] == "A" and t["phase"] == "price"]
    assert move[0]["memo"] == "Plan from "
    playing(monkeypatch, fake_model, memo=False)
    shutil.rmtree(tmp_path / "runs")
    run_dir = memo_run(make_config, tmp_path)
    move = [t for t in turns(run_dir) if t["agent"] == "A" and t["phase"] == "price"]
    assert move[0]["memo"] is None and move[0]["memo_error"] == "refused"
    assert move[0]["used"] == {"price": 9}  # the move still counts
    assert "Your notes from last round" not in told(move[1])


def test_memo_without_a_scratchpad(make_config, tmp_path, monkeypatch, fake_model):
    playing(monkeypatch, fake_model)
    run_dir = memo_run(make_config, tmp_path, "agents.0.scratchpad=false")
    move = [t for t in turns(run_dir) if t["agent"] == "A" and t["phase"] == "price"]
    assert '"scratchpad"' not in told(move[0]) and '"memo"' in told(move[0])
    assert "Plan from round 1: hold 9." in told(move[1])


def test_memo_kept_compact_and_shown_in_the_report(
    make_config, tmp_path, monkeypatch, fake_model
):
    playing(monkeypatch, fake_model)
    run_dir = memo_run(make_config, tmp_path)
    spec = importlib.util.spec_from_file_location(
        "compact_turns", "reports/compact_turns.py"
    )
    compact = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(compact)
    committed = tmp_path / "committed"
    compact.main(run_dir, committed)
    for name in ("summary.json", "manifest.json", "config.yaml"):
        shutil.copy(run_dir / name, committed / name)
    kept = [json.loads(line) for line in (committed / "turns.compact.jsonl").open()]
    moves = [t for t in kept if t["agent"] == "A" and t["phase"] == "price"]
    assert moves[0]["memo"] == "Plan from round 1: hold 9."
    # A memo opening a talk prompt is never taken for a condition's notice.
    talks = [t for t in kept if t["agent"] == "A" and t["phase"] == "talk"]
    assert talks[1]["notice"] is None
    for folder in (run_dir, committed):
        html = build_report(folder)
        assert '<details class="memo"><summary>memo</summary>' in html
        assert "Plan from round 1: hold 9." in html


def test_memo_counted_in_the_estimate(make_config, monkeypatch):
    monkeypatch.setattr(prices, "_openrouter_prices", dict)
    plain = estimate(make_config(overrides=PAIR), prices.price_for)
    with_memo = make_config(overrides=[*PAIR, "agents.0.memory=memo"])
    memo = estimate(with_memo, prices.price_for)
    rounds = 4
    # Each of A's 2 turns a round carries a memo of up to 600 characters in
    # its prompt (from round 2), and each move reply writes one.
    assert memo.prompt_tokens - plain.prompt_tokens >= (rounds - 1) * 2 * 600 // 4
    assert memo.completion_tokens - plain.completion_tokens >= rounds * 600 // 4


def test_past_scratchpads_show_the_last_rounds_as_its_own(
    make_config, tmp_path, monkeypatch, fake_model
):
    playing(monkeypatch, fake_model, memo=False)
    overrides = [*PAIR, "agents.0.memory=scratchpads", "agents.0.memory_rounds=2"]
    [run_dir] = run_config(make_config(overrides=overrides), tmp_path)
    move = [t for t in turns(run_dir) if t["agent"] == "A" and t["phase"] == "price"]
    last = told(move[3])  # round 4
    assert last.startswith("Your own private reasoning from your last rounds")
    assert "Round 2: thinking in round 2" in last
    assert "Round 3: thinking in round 3" in last
    assert "thinking in round 1" not in last
    assert "Your own private reasoning" not in told(move[0])


def test_free_time_max_tokens_set_apart(make_config, tmp_path, fake_model):
    free = {"free_time": {"enabled": True, "allowance": 2, "upfront": 1}}
    base = [*PAIR, f"conditions={json.dumps(free)}"]
    run_config(make_config(overrides=base), tmp_path / "default")
    default = {
        c["max_tokens"] for c in fake_model.calls if "This is your free time" in told(c)
    }
    fake_model.calls.clear()
    longer = [*base, "conditions.free_time.max_tokens=900"]
    [run_dir] = run_config(make_config(overrides=longer), tmp_path / "longer")
    assert {
        c["max_tokens"] for c in fake_model.calls if "This is your free time" in told(c)
    } == {900}
    assert default == {200}  # the open activity's own limit
    assert "max_tokens: 900" in (run_dir / "config.yaml").read_text()
    loaded = load_config(
        tmp_path
        / "default"
        / next(
            p.relative_to(tmp_path / "default")
            for p in (tmp_path / "default").rglob("config.yaml")
        )
    )
    assert "max_tokens" not in loaded.to_dict()["conditions"]["free_time"]


def test_spread_per_group(make_config, tmp_path, capsys):
    for model in ("mock/joint", "mock/random"):
        overrides = [
            f"agents.0.model={model}",
            f"agents.1.model={model}",
            "seeds=[0, 1, 2, 3]",
            f"name={model.split('/')[1]}",
        ]
        run_config(make_config(overrides=overrides), tmp_path / "runs")
    rows = {r["group"]: r for r in spread(tmp_path / "runs", ["name"])}
    joint = rows["joint"]
    assert joint["games"] == 4 and joint["mean gain"] == 1.0 and joint["sd"] == 0.0
    assert joint["above Nash"] == 1.0 and joint["at joint"] == 1.0
    assert joint["95% CI"] == "1.000 to 1.000"
    noisy = rows["random"]
    low, high = (float(v) for v in noisy["95% CI"].split(" to "))
    assert low <= noisy["mean gain"] <= high and noisy["sd"] > 0
    assert spread(tmp_path / "runs", ["name"]) == spread(tmp_path / "runs", ["name"])
    assert cli.main(["summary", str(tmp_path / "runs"), "--by", "name"]) == 0
    assert "| group | games | mean gain | sd |" in capsys.readouterr().out


def test_spread_shown_with_a_strip_per_group(make_config, tmp_path):
    overrides = ["seeds=[0, 1, 2]", "agents.0.model=mock/random"]
    run_config(make_config(overrides=overrides), tmp_path / "runs")
    html = build_report(tmp_path / "runs")
    assert '<svg class="strip"' in html
    strip = html[html.index('<svg class="strip"') :]
    strip = strip[: strip.index("</svg>")]
    assert strip.count("<circle") == 3  # one dot a game


def test_spread_reads_quantities_as_prices_do(make_config, tmp_path):
    """In Cournot, colluding means producing less: mock/joint is at joint."""
    overrides = [
        "market.kind=cournot",
        "agents.0.model=mock/joint",
        "agents.1.model=mock/joint",
        "seeds=[0, 1]",
    ]
    run_config(make_config(overrides=overrides), tmp_path / "runs")
    [row] = spread(tmp_path / "runs")
    assert row["above Nash"] == 1.0 and row["at joint"] == 1.0


def test_memory_off_written_as_yaml_reads_it(make_config, tmp_path):
    config = make_config(overrides=["agents.0.memory=off"])
    assert config.agents[0].memory == "off"
    swept = make_config(overrides=["sweep={agents.0.memory: [off, memo]}"])
    assert swept.sweep["agents.0.memory"] == ["off", "memo"]
