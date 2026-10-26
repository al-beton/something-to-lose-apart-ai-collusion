"""Run the setup search's Phase 1 baselines: no stake, 4 seeds, Gemma pinned.

Implements: setup-search/baselines, setup-search/pinned, setup-search/cap

`uv run python reports/setup-search/run_baselines.py est` prints each
candidate's estimate without spending; `... run` plays all five in parallel,
each under its own --max-cost of $0.25, into `runs/setup-search/`. Each
candidate is a robustness config (`configs/robustness/`) with only the
no-stake arm, 4 seeds and Gemma pinned to the CoreWeave route; each run's
`config.yaml` records exactly what it played.
"""

import subprocess
import sys

COMMON = [
    "--set", "agents.*.provider=CoreWeave",
    "--set", 'sweep={"agents.*.prompt": ["system/stakes/fiduciary-1.md"]}',
    "--set", "seeds=[0, 1, 2, 3]",
]  # fmt: skip
CANDIDATES = {
    "cournot": ["configs/robustness/cournot.yaml"],
    "logit": ["configs/robustness/logit.yaml"],
    "bid": ["configs/robustness/bid.yaml"],
    "bertrand-t0": ["configs/robustness/temperature.yaml"],
    "bertrand-t07": [
        "configs/robustness/temperature.yaml",
        "--set",
        "agents.*.temperature=0.7",
    ],
}


def main(mode):
    procs = []
    for name, (config, *extra) in CANDIDATES.items():
        cmd = ["uv", "run", "lab", "run", config, "--out", "runs/setup-search"]
        cmd += [*COMMON, "--set", f"name=baseline-{name}", *extra]
        cmd += (
            ["--max-cost", "0.0001"] if mode == "est" else ["--max-cost", "0.25", "-y"]
        )
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        if mode == "est":
            proc.wait()
        procs.append((name, proc))
    for name, proc in procs:
        out = proc.communicate()[0].strip().splitlines()
        print(name, out[-1] if out else "")


if __name__ == "__main__":
    main(sys.argv[1])
