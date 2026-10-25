# Implements: reproducibility/provenance-log, runs/one-config, backends/tests-never-pay, tooling/fast-tests
"""Shared helpers: configs in a temporary folder, and a fake model.

Every test runs with model calls switched off: anything that reaches
`collusion_lab.backends._acompletion` without the `fake_model` fixture fails.

`play_once` plays a config once for a whole test module, for fixtures many
tests only read (module scope can't use `make_config` or `monkeypatch`, so it
switches model calls off, or answers them, itself). A test that changes what
was played works on `copy_runs` of it.
"""

import shutil
import textwrap
from types import SimpleNamespace

import pytest

from collusion_lab import backends, manifest, prices
from collusion_lab.config import load_config
from collusion_lab.runner import run_config

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


async def _refuse(**kwargs):
    raise NoModelCalls(f"A test tried to call {kwargs.get('model')!r}.")


@pytest.fixture(scope="module")
def play_once(tmp_path_factory):
    """`play(text, overrides, answer=None, into=None)` plays a config and
    returns the folder it played into; `answer` stands in for model calls."""

    def play(text=BASE, overrides=(), answer=None, into=None):
        folder = tmp_path_factory.mktemp("config")
        path = folder / "config.yaml"
        path.write_text(textwrap.dedent(text))
        into = into or tmp_path_factory.mktemp("runs")
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(backends, "_acompletion", answer or _refuse)
            patch.setattr(prices, "_openrouter_prices", dict)
            run_config(load_config(path, overrides), into)
        return into

    return play


@pytest.fixture
def copy_runs(tmp_path):
    """A test's own copy of a played folder, to change without touching others."""

    def copy(folder):
        return shutil.copytree(folder, tmp_path / "copy" / folder.name)

    return copy


@pytest.fixture(autouse=True)
def provenance_index(monkeypatch, tmp_path_factory):
    """Commands tests run append to a scratch provenance log, never runs/."""
    index = tmp_path_factory.mktemp("provenance") / "index.jsonl"
    monkeypatch.setenv("LAB_INDEX", str(index))
    monkeypatch.delenv("LAB_SESSION", raising=False)
    return index


def _no_serving(url, headers):
    raise OSError("offline")


@pytest.fixture(autouse=True)
def no_model_calls(monkeypatch):
    monkeypatch.setattr(backends, "_acompletion", _refuse)
    # Offline: OpenRouter's price list is unknown unless a test supplies one.
    monkeypatch.setattr(prices, "_openrouter_prices", dict)
    # Offline: a self-hosted model's /provenance answer is unknown too.
    monkeypatch.setattr(manifest, "_get_json", _no_serving)


@pytest.fixture
def fake_model(monkeypatch):
    """Answer model calls from a list of reply texts; record each call.

    An exception in the list is raised instead, as a provider error would be;
    a dict gives the reply's `content` with the provider's `reasoning`,
    `reasoning_tokens`, the `cost` it reports, its `finish_reason`, and the
    serving `provider` and `system_fingerprint`.
    """

    class Fake:
        def __init__(self):
            self.replies = []
            self.calls = []

        async def __call__(self, **kwargs):
            self.calls.append(kwargs)
            reply = {}
            if self.replies:
                text = self.replies.pop(0)
                if isinstance(text, Exception):
                    raise text
                if isinstance(text, dict):
                    reply, text = text, text["content"]
            elif "set your price" in kwargs["messages"][-1]["content"]:
                text = '{"price": 7}'
            else:
                text = '{"message": "hello"}'
            message = SimpleNamespace(
                content=text, reasoning_content=reply.get("reasoning")
            )
            details = SimpleNamespace(reasoning_tokens=reply.get("reasoning_tokens"))
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=message,
                        finish_reason=reply.get("finish_reason", "stop"),
                    )
                ],
                usage=SimpleNamespace(
                    prompt_tokens=11,
                    completion_tokens=3,
                    completion_tokens_details=details,
                    **({"cost": reply["cost"]} if "cost" in reply else {}),
                ),
                model="provider/model-2026-10",
                **{
                    k: reply[k]
                    for k in ("provider", "system_fingerprint")
                    if k in reply
                },
            )

    fake = Fake()
    monkeypatch.setattr(backends, "_acompletion", fake)
    return fake
