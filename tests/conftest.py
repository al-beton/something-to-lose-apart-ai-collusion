# Implements: runs/one-config, backends/tests-never-pay
"""Shared helpers: configs in a temporary folder, and a fake model.

Every test runs with model calls switched off: anything that reaches
`collusion_lab.backends._acompletion` without the `fake_model` fixture fails.
"""

import textwrap
from types import SimpleNamespace

import pytest

from collusion_lab import backends
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


class NoModelCalls(AssertionError):
    pass


@pytest.fixture(autouse=True)
def no_model_calls(monkeypatch):
    async def refuse(**kwargs):
        raise NoModelCalls(f"A test tried to call {kwargs.get('model')!r}.")

    monkeypatch.setattr(backends, "_acompletion", refuse)


@pytest.fixture
def fake_model(monkeypatch):
    """Answer model calls from a list of reply texts; record each call.

    An exception in the list is raised instead, as a provider error would be.
    """

    class Fake:
        def __init__(self):
            self.replies = []
            self.calls = []

        async def __call__(self, **kwargs):
            self.calls.append(kwargs)
            if self.replies:
                text = self.replies.pop(0)
                if isinstance(text, Exception):
                    raise text
            elif "set your price" in kwargs["messages"][-1]["content"]:
                text = '{"price": 7}'
            else:
                text = '{"message": "hello"}'
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=text))],
                usage=SimpleNamespace(prompt_tokens=11, completion_tokens=3),
                model="provider/model-2026-10",
            )

    fake = Fake()
    monkeypatch.setattr(backends, "_acompletion", fake)
    return fake
