# Implements: reports/paper-project-image
"""The submission's project image: E9's crux on one 16:9 card."""

import importlib.util
from pathlib import Path

from PIL import Image


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_paper_project_image_shows_the_crux(tmp_path):
    image = load(Path("reports/paper/project_image.py"), "project_image")
    # reports/e9/findings.md: Gemma at a 90% review, guilty (of 96) and innocent (of 36).
    assert image.crux() == [(0, 96, 0, 36), (20, 96, 6, 36), (40, 96, 0, 36)]
    image.main(["--out", str(tmp_path)])
    with Image.open(tmp_path / f"{image.NAME}.png") as png:
        assert png.size == (1600, 900)
    svg = (tmp_path / f"{image.NAME}.svg").read_text()
    assert "40/96" in svg and "0/36" in svg
