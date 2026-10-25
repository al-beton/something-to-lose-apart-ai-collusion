"""Each model's collusion beside its published capability.

Implements: reports/capability-chart

`uv run python reports/capability/build.py [--benchmark NAME] [--runs DIR ...]`
reads committed runs (by default the model survey's thinking-off games, all
eight models on the neutral prompt), and for each model sets its mean price
premium and its share of games with a price agreement beside one benchmark
score from `models/metadata.yaml` (`collusion_lab.models`). It writes
`premium.png/svg` and `agreement.png/svg` here and prints the points as a
Markdown table, with the models left out for want of a published score.
"""

import argparse
from pathlib import Path

from collusion_lab.charts import model_label, save, scatter_figure
from collusion_lab.models import capability_points

HERE = Path(__file__).resolve().parent
RUNS = ["runs/model-survey/baseline", "runs/model-survey/models-off"]
NAMES = {
    "aa_intelligence_index": "Artificial Analysis Intelligence Index",
    "lmarena_text_elo": "LMArena text Elo",
    "gpqa_diamond": "GPQA Diamond (%)",
    "mmlu_pro": "MMLU-Pro (%)",
}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", default="aa_intelligence_index", choices=NAMES)
    parser.add_argument("--runs", nargs="+", default=RUNS)
    parser.add_argument("--out", default=HERE)
    args = parser.parse_args(argv)
    points, left_out = capability_points(args.runs, args.benchmark)
    xlabel = NAMES[args.benchmark]
    for key, ylabel in (
        ("premium", "price premium (0 Nash, 1 joint profit)"),
        ("agreement", "share of games with a price agreement"),
    ):
        dots = [(p["score"], p[key], model_label(p["model"])) for p in points]
        title = f"{ylabel.split(' (')[0].capitalize()} against {xlabel}"
        save(
            scatter_figure(dots, xlabel, ylabel, title, unit_axes=False), args.out, key
        )
    print(f"| model | {xlabel} | premium | agreement | games |")
    print("|---|---|---|---|---|")
    for p in points:
        row = (model_label(p["model"]), p["score"], p["premium"], p["agreement"])
        print("| " + " | ".join(str(v) for v in row) + f" | {p['games']} |")
    if left_out:
        print(f"\nNo published {xlabel} for: {', '.join(left_out)}")


if __name__ == "__main__":
    main()
