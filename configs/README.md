<!-- Implements: specs-and-docs/folder-guides -->
# Configs

One YAML file per experiment, or a folder of them: the market, each agent's model, prompt and temperature, the seeds, the conditions (audits, stakes, free time) and the arms of a sweep. Each file's header says what it runs and how.

- **To start:** `smoke.yaml` (scripted firms, free) and `cheap.yaml` (one cheap model).
- **The paper's experiments:** `e4-*.yaml`, `e9/spike.yaml` and `e7-way-out.yaml`; the other folders are the rest of the experiments in `experiments/spec/`.
- **Markets:** `scenarios/` has one config per market (`logit`, `cournot`, `bid`, and a price board).
- **Our own GPUs:** `modal.yaml`.

`uv run lab run <config> --set path=value` changes one value for a run. The fields are in `src/collusion_lab/config.py`.
