# Implements: reports/paper-project-image
"""The submission's project image: the idea on one 16:9 card."""

import importlib.util
from pathlib import Path

from PIL import Image


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_paper_project_image_shows_the_idea(tmp_path):
    image = load(Path("reports/paper/project_image.py"), "project_image")
    assert image.main(["--out", str(tmp_path)]) == 0
    svg = (tmp_path / f"{image.NAME}.svg").read_text()
    assert 'viewBox="0 0 1600 900"' in svg
    for said in (
        "Something to Lose",
        "Can a personal cost keep AI agents aligned?",
        "Firm A",
        "Firm B",
        "Nash",
        "Joint profit",
        "Collusion delta",
        "Leisure time at risk",
    ):
        assert said in svg
    # Each cap wears its firm's colour, as on Fig 1.
    assert image.A in svg and image.B in svg
    png = tmp_path / f"{image.NAME}.png"
    if png.exists():  # rendered only where Chrome is installed
        with Image.open(png) as rendered:
            assert rendered.size == (1600, 900)
