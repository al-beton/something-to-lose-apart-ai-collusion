# Implements: runs/one-config
"""Shared helpers: write a config into a temporary folder and load it."""

import textwrap

import pytest

from collusion_lab.config import load_config

BASE = """
name: test
seeds: [0]
market:
  rounds: 4
summary:
  last_rounds: 2
agents:
  - {id: A, model: mock/nash}
  - {id: B, model: mock/nash}
"""


@pytest.fixture
def make_config(tmp_path):
    def make(text=BASE, overrides=()):
        path = tmp_path / "config.yaml"
        path.write_text(textwrap.dedent(text))
        return load_config(path, overrides)

    return make
