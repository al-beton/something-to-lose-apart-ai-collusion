# Implements: backends/model-metadata, reports/capability-chart
"""Published facts about the models the lab uses, and their behaviour beside them.

`metadata()` reads `models/metadata.yaml`: by model id, the provider, release
date, open weights (with the parameter count when published) and a few
benchmark scores. Each fact is `{value, source, quote, retrieved}` (the URL
it was read from, the words it was read in, the date), or a null value with a
`note` saying why it's blank: a figure no source publishes is never
estimated. An entry can say `same_as: <id>` for the same model served
elsewhere (the Modal Mistral is OpenRouter's Mistral Small 3.2).

`capability_points(folders, benchmark)` sets each model's behaviour in
committed runs beside one benchmark: its mean price premium (model firms
only, `charts.run_premium`) and the share of its games with a price agreement
(the report's `agreement` rule), from games where both firms are that model.
Models with no published score for the benchmark are listed apart, never
plotted. `reports/capability/build.py` draws them.
"""

from pathlib import Path
from statistics import mean

import yaml

from collusion_lab.charts import run_premium
from collusion_lab.report.games import load_games
from collusion_lab.report.highlights import find_highlights

METADATA = Path(__file__).resolve().parents[2] / "models" / "metadata.yaml"


def metadata(path=METADATA):
    """{model id: its entry}, with `same_as` entries spelled out."""
    data = yaml.safe_load(Path(path).read_text())
    return {
        model: data[entry["same_as"]] if "same_as" in entry else entry
        for model, entry in data.items()
    }


def capability_points(folders, benchmark, known=None):
    """([{model, score, premium, agreement, games}], [models with no score])."""
    known = metadata() if known is None else known
    seen = {}
    for game in load_games(folders):
        models = {agent["model"] for agent in game.config["agents"]}
        if len(models) != 1:  # a mixed pair says nothing about one model
            continue
        [model] = models
        agreed = any(h.kind == "agreement" for h in find_highlights(game))
        seen.setdefault(model, []).append((run_premium(game.dir), agreed))
    points, left_out = [], []
    for model, games in sorted(seen.items()):
        fact = (known.get(model) or {}).get("benchmarks", {}).get(benchmark) or {}
        if fact.get("value") is None:
            left_out.append(model)
            continue
        points.append(
            {
                "model": model,
                "score": fact["value"],
                "premium": round(mean(p for p, _ in games), 3),
                "agreement": round(sum(a for _, a in games) / len(games), 3),
                "games": len(games),
            }
        )
    return points, left_out
