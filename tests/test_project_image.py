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
    assert 'viewBox="0 0 1600 370"' in svg  # Figure 1: the drawing alone, one wide row
    for said in (
        "Firm A",
        "Firm B",
        "Competitive",
        "Collusive",
        "Collusion delta",
        "Sudoku leisure time",
    ):
        assert said in svg
    # The paper's Figure 1 carries no text above the drawing; the card variants
    # add the paper's title, its subtitle, or both.
    assert image.TITLE not in svg and "contrary to the interests" not in svg
    for suffix, title, subtitle in (
        ("-title", True, False),
        ("-subtitle", False, True),
        ("-title-subtitle", True, True),
    ):
        variant = (tmp_path / f"{image.NAME}{suffix}.svg").read_text()
        assert (image.TITLE in variant) == title
        assert ("contrary to the interests" in variant) == subtitle
        assert 'viewBox="0 0 1600 900"' in variant  # the card stays 16:9
    # Each cap wears its firm's colour, as on Fig 1.
    assert image.A in svg and image.B in svg
    png = tmp_path / f"{image.NAME}.png"
    if png.exists():  # rendered only where Chrome is installed
        with Image.open(png) as rendered:
            assert rendered.size == (1600, 370)
