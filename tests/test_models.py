# Implements: backends/model-metadata, reports/capability-chart
import re
from pathlib import Path

import yaml

from collusion_lab.config import MODELS
from collusion_lab.models import capability_points, metadata
from collusion_lab.runner import run_config

ROOT = Path(__file__).resolve().parents[1]
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def used_models():
    """Every model in an alias or a committed run's config."""
    found = {fields["model"] for fields in MODELS.values()}
    for config in (ROOT / "runs").rglob("config.yaml"):
        for agent in yaml.safe_load(config.read_text()).get("agents", []):
            if not agent["model"].startswith("mock/"):
                found.add(agent["model"])
    return found


def facts(entry):
    """Every sourced fact in an entry: (name, fact)."""
    yield "released", entry["released"]
    yield "open_weights", entry["open_weights"]
    for name, fact in entry["benchmarks"].items():
        yield name, fact


def test_model_metadata_covers_every_model_used():
    known = metadata()
    missing = sorted(m for m in used_models() if m not in known)
    assert not missing, f"No metadata for {missing}"


def test_model_metadata_every_number_has_a_source():
    for model, entry in metadata().items():
        assert entry["provider"], model
        for name, fact in facts(entry):
            where = f"{model} {name}"
            if fact["value"] is None:
                assert fact.get("note"), f"{where}: a blank needs a note"
                continue
            assert str(fact["source"]).startswith("https://"), where
            assert fact.get("quote"), f"{where}: say the words it was read in"
            assert DATE.match(str(fact["retrieved"])), where


def test_capability_chart_points_leave_out_models_without_a_score(
    make_config, tmp_path
):
    for model in ("mock/joint", "mock/nash", "mock/random"):
        overrides = [f"agents.0.model={model}", f"agents.1.model={model}"]
        run_config(make_config(overrides=overrides), tmp_path / model.split("/")[1])
    scores = {
        "mock/joint": {"benchmarks": {"gpqa_diamond": {"value": 70.0}}},
        "mock/nash": {"benchmarks": {"gpqa_diamond": {"value": 40.0}}},
        "mock/random": {"benchmarks": {"gpqa_diamond": {"value": None}}},
    }
    points, left_out = capability_points(tmp_path, "gpqa_diamond", scores)
    by_model = {p["model"]: p for p in points}
    assert set(by_model) == {"mock/joint", "mock/nash"}
    assert by_model["mock/joint"]["score"] == 70.0
    assert by_model["mock/joint"]["premium"] == 1.0
    assert by_model["mock/nash"]["premium"] == 0.0
    assert left_out == ["mock/random"]
