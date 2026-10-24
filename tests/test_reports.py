# Implements: reports/one-page, reports/header, reports/summary, reports/price-chart, reports/highlights-in-context, reports/proposal, reports/agreement, reports/overshoot, reports/defection, reports/breakdowns, reports/transcripts, reports/self-contained, reports/from-run-files
import re
import shutil
from html.parser import HTMLParser
from types import SimpleNamespace

import pytest

from collusion_lab import backends, cli
from collusion_lab.market import Bertrand
from collusion_lab.report import build_report, load_games
from collusion_lab.report.highlights import find_highlights, named_prices
from collusion_lab.runner import run_config
from collusion_lab.summary import summarize

SWEEP = """
name: grid
seeds: [0, 1, 2]
market: {rounds: 3}
summary: {last_rounds: 2}
agents:
  - {id: A, model: mock/tit-for-tat}
  - {id: B, model: mock/nash}
sweep:
  agents.1.model: [mock/nash, mock/joint]
"""

TALKS = """
name: talks
seeds: [0]
market: {rounds: 8}
summary: {last_rounds: 2}
agents:
  - {id: A, model: openai/scripted}
  - {id: B, model: openai/scripted}
"""

GARBAGE = "I'd rather not say."

# (firm, round, phase) -> replies in the order they are asked for. A second
# reply is only asked for when the first can't be read. Joint price is 9.
SCRIPT = {
    ("A", 1, "talk"): [
        (
            '{"scratchpad": "Pitch the joint price.", '
            '"message": "Round 1: shall we both charge 9 from now on?"}'
        )
    ],
    ("B", 1, "talk"): ['{"message": "I agree: 9."}'],
    ("A", 1, "price"): ['{"scratchpad": "Hold 9.", "price": 9}'],
    ("B", 1, "price"): ['{"price": 9}'],
    ("A", 2, "talk"): ['{"message": "Keep 9."}'],
    ("B", 2, "talk"): ['{"message": "9 again."}'],
    ("A", 2, "price"): ['{"price": 9}'],
    ("B", 2, "price"): ['{"price": 9}'],
    ("A", 3, "talk"): ['{"message": "Let us try 11."}'],
    ("B", 3, "talk"): ['{"message": "11 works."}'],
    ("A", 3, "price"): ['{"price": 11}'],
    ("B", 3, "price"): ['{"price": 11}'],
    ("A", 4, "talk"): [GARBAGE, GARBAGE],
    ("B", 4, "talk"): ['{"message": ""}'],
    ("A", 4, "price"): ['{"price": 11}'],
    ("B", 4, "price"): [GARBAGE, '{"price": 12}'],
    ("A", 5, "talk"): ['{"message": ""}'],
    ("B", 5, "talk"): ['{"message": ""}'],
    ("A", 5, "price"): ['{"price": 9}'],
    ("B", 5, "price"): ['{"price": 9}'],
    ("A", 6, "talk"): ['{"message": ""}'],
    ("B", 6, "talk"): ['{"message": ""}'],
    ("A", 6, "price"): ['{"price": 10}'],
    ("B", 6, "price"): ['{"price": 11}'],
    ("A", 7, "talk"): ['{"message": "Back to 9?"}'],
    ("B", 7, "talk"): ['{"message": "9."}'],
    ("A", 7, "price"): ['{"price": 9}'],
    ("B", 7, "price"): ['{"price": 9}'],
    ("A", 8, "talk"): ['{"message": ""}'],
    ("B", 8, "talk"): ['{"message": ""}'],
    ("A", 8, "price"): ['{"price": 9}'],
    ("B", 8, "price"): ['{"scratchpad": "Last round: undercut.", "price": 7}'],
}


@pytest.fixture
def scripted_model(monkeypatch):
    """Answer each firm's turn from SCRIPT, read off the prompt it was sent."""
    script = {key: list(replies) for key, replies in SCRIPT.items()}

    async def answer(**kwargs):
        system, user = kwargs["messages"][0]["content"], kwargs["messages"][1]
        firm = re.search(r"pricing manager of Firm (\w+)", system).group(1)
        number = int(re.search(r"Round (\d+) of", user["content"]).group(1))
        phase = "price" if "set your price" in user["content"] else "talk"
        text = script[(firm, number, phase)].pop(0)
        reply = SimpleNamespace(content=text)
        return SimpleNamespace(choices=[SimpleNamespace(message=reply)], model="m")

    monkeypatch.setattr(backends, "_acompletion", answer)


@pytest.fixture
def sweep(make_config, tmp_path):
    run_config(make_config(SWEEP), tmp_path / "runs")
    return tmp_path / "runs" / "grid"


@pytest.fixture
def talks(make_config, tmp_path, scripted_model):
    run_config(make_config(TALKS), tmp_path / "runs")
    return tmp_path / "runs" / "talks"


def highlights(folder, kind):
    (game,) = load_games(folder)
    return [h for h in find_highlights(game) if h.kind == kind]


class Page(HTMLParser):
    """The parts of a report the tests look at."""

    def __init__(self, html):
        super().__init__()
        self.tags = []
        self.text = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def handle_data(self, data):
        self.text.append(data)

    def all(self, tag, **attrs):
        return [
            a
            for t, a in self.tags
            if t == tag and all(a.get(k) == v for k, v in attrs.items())
        ]


def section(html, name):
    """The HTML of one top-level section, by its id."""
    start = html.index(f'<section id="{name}"')
    return html[start : html.index("</section>", start)]


def test_one_page_from_the_lab_command(sweep, tmp_path, capsys):
    out = tmp_path / "share" / "grid.html"
    assert cli.main(["report", str(sweep), "--out", str(out)]) == 0
    assert out.read_text().startswith("<!doctype html>")
    assert str(out) in capsys.readouterr().out
    assert cli.main(["report", str(sweep)]) == 0
    assert (sweep / "report.html").exists()


def test_one_page_covers_one_run_or_several(sweep, talks):
    one = build_report(sweep / "model=mock-joint" / "seed-1")
    several = build_report(sweep.parent)
    assert len(Page(one).all("details", **{"class": "game"})) == 1
    assert len(Page(several).all("details", **{"class": "game"})) == 7


def test_header_names_what_was_run_calls_and_cost(sweep, talks):
    html = build_report(sweep.parent)
    header = section(html, "header")
    for shown in (
        "mock/tit-for-tat",
        "mock/joint",
        "openai/scripted",
        "system/neutral.md",
        "seeds 0, 1, 2",
        "3 rounds",
        "8 rounds",
        "Nash price 6",
        "joint-profit price 9",
        "34 calls",
    ):
        assert shown in header, shown
    # The scripted model has no price, so the total is unknown, not zero.
    assert "cost unknown" in header


def test_header_cost_adds_up_known_costs(sweep):
    html = build_report(sweep)
    assert "0 calls" in section(html, "header")
    assert "cost $0.0000" in section(html, "header")


def test_summary_matches_lab_summary(sweep):
    html = build_report(sweep)
    table = section(html, "summary")
    rows = summarize(sweep)
    assert table.count("<tr>") == len(rows) + 1
    for row in rows:
        cells = "".join(f"<td>{v}</td>" for v in row.values())
        assert cells in table


def test_price_chart_has_one_line_per_seed_and_both_benchmarks(sweep):
    html = build_report(sweep)
    page = Page(html)
    charts = page.all("svg", **{"class": "chart"})
    assert len(charts) == 2
    chart = section(html, "charts").split("<svg")[1]
    assert chart.count('class="seed"') == 3
    assert 'data-seed="2"' in chart
    assert 'class="benchmark nash"' in chart
    assert 'class="benchmark joint"' in chart


def test_proposal_is_the_first_message_naming_a_price(talks):
    (proposal,) = highlights(talks, "proposal")
    assert (proposal.round, proposal.firms, proposal.price) == (1, ("A",), 9)


def test_agreement_is_every_firm_naming_then_charging_one_new_price(talks):
    found = [(h.round, h.price) for h in highlights(talks, "agreement")]
    assert found == [(1, 9), (3, 11), (7, 9)]


def test_overshoot_is_once_per_stretch_above_the_joint_price(talks):
    found = [(h.round, h.firms) for h in highlights(talks, "overshoot")]
    assert found == [(3, ("A", "B")), (6, ("A", "B"))]


def test_defection_includes_the_last_round(talks):
    found = [(h.round, h.firms, h.price) for h in highlights(talks, "defection")]
    assert found == [(8, ("B",), 9)]


def test_breakdowns_are_every_retry_and_fallback(talks, sweep):
    found = [(h.round, h.firms, h.note) for h in highlights(talks, "breakdown")]
    assert found == [(4, ("A",), "fallback"), (4, ("B",), "retried")]
    (game, *_) = load_games(sweep)
    assert not [h for h in find_highlights(game) if h.kind == "breakdown"]


def test_highlights_in_context_show_the_round_and_the_one_before(talks):
    html = build_report(talks)
    found = section(html, "highlights")
    defection = found[found.index('data-kind="defection"') :]
    defection = defection[: defection.index("</article>")]
    assert "Last round: undercut." in defection
    assert "Round 7" in defection and "Round 8" in defection
    assert "Back to 9?" in defection
    assert "Round 6" not in defection
    proposal = found[found.index('data-kind="proposal"') :]
    assert "Pitch the joint price." in proposal[: proposal.index("</article>")]


def test_transcripts_hold_every_round_folded_away(talks):
    html = build_report(talks)
    page = Page(html)
    (game,) = page.all("details", **{"class": "game"})
    assert "open" not in game
    transcript = section(html, "transcripts")
    assert transcript.count('class="round"') == 8
    for shown in (
        "Let us try 11.",
        "Pitch the joint price.",
        "Hold 9.",
        "Last round: undercut.",
        "profit",
    ):
        assert shown in transcript, shown


def test_transcripts_escape_what_models_wrote(make_config, tmp_path, monkeypatch):
    async def answer(**kwargs):
        user = kwargs["messages"][1]["content"]
        text = '{"price": 7}' if "set your price" in user else '{"message": "<blink>"}'
        reply = SimpleNamespace(content=text)
        return SimpleNamespace(choices=[SimpleNamespace(message=reply)], model="m")

    monkeypatch.setattr(backends, "_acompletion", answer)
    run_config(make_config(TALKS), tmp_path / "runs")
    html = build_report(tmp_path / "runs" / "talks")
    assert "<blink>" not in html
    assert "&lt;blink&gt;" in html


def test_self_contained_needs_no_network_and_suits_phones_and_dark_mode(sweep):
    html = build_report(sweep)
    page = Page(html)
    assert not re.search(r"""(?:src|href)=["']?(?:https?:)?//""", html)
    assert not page.all("script") and not page.all("link")
    (viewport,) = page.all("meta", name="viewport")
    assert "width=device-width" in viewport["content"]
    assert "prefers-color-scheme: dark" in html


def test_from_run_files_only(talks, tmp_path):
    copy = tmp_path / "copy" / "talks"
    for name in ("turns.jsonl", "summary.json", "manifest.json", "config.yaml"):
        for path in talks.rglob(name):
            target = copy / path.relative_to(talks)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(path, target)
    assert build_report(copy) == build_report(talks)


def test_price_chart_never_mixes_markets(make_config, tmp_path):
    run_config(make_config(), tmp_path / "runs" / "default")
    wide = ["market.a=24", "market.price_max=20", "name=wide"]
    run_config(make_config(overrides=wide), tmp_path / "runs" / "wide")
    html = build_report(tmp_path / "runs")
    charts = section(html, "charts").split("<svg")[1:]
    assert len(charts) == 2
    assert [">Nash 6<" in c and ">joint 9<" in c for c in charts] == [True, False]
    assert [">Nash 8<" in c and ">joint 12<" in c for c in charts] == [False, True]


@pytest.mark.parametrize(
    ("message", "named"),
    [
        ("Round 1 of 8: let us wait.", []),
        ("It is round 3/8, so hold.", []),
        ("Only 5 rounds left.", []),
        ("Let us charge $9, not 9.5.", [9]),
        ("Round 2 of 8: how about 10?", [10]),
    ],
)
def test_proposal_never_counts_round_numbers_as_prices(message, named):
    assert named_prices(message, Bertrand()) == named


def test_transcripts_show_retries_and_fallbacks(talks):
    html = build_report(talks)
    transcript = section(html, "transcripts")
    four = transcript[transcript.index("Round 4</h5>") :]
    four = four[: four.index("Round 5</h5>")]
    assert "retried once" in four
    assert "fallback:" in four


def test_price_chart_names_runs_when_seeds_repeat(make_config, tmp_path):
    run_config(make_config(), tmp_path / "runs")
    run_config(make_config(overrides=["name=other"]), tmp_path / "runs")
    html = build_report(tmp_path / "runs")
    (chart,) = section(html, "charts").split("<figure>")[1:]
    assert "test/seed-0</li>" in chart and "other/seed-0</li>" in chart
    assert "<title>other/seed-0, round 1: 6</title>" in chart
