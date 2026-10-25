# Implements: backends/reasoning-in-estimate, backends/serving-provider-logged, backends/pinned-route, reproducibility/response-cache, reproducibility/cache-modes, logs/reasoning-logged, agents/json-mode
"""A response cache, so a seeded run can be replayed exactly and for free.

Provider seeds are best-effort (some providers ignore them, and even
temperature 0 isn't guaranteed deterministic), so exact replay comes from
storing replies. A reply is keyed by everything that shaped it: model,
address, messages, temperature, token limit, seed and attempt, plus the agent
asking, so two agents asked identical questions at once never share a slot.
An agent's reasoning setting and JSON mode join the key only when set, so
replies stored before they existed still match. The reasoning text and the
finish reason are stored with the reply, and so is what asked for it
(`about`: model, reasoning setting, phase), which the cost estimate reads
through `observed()` and replay never does. Re-running the
same config and seed asks the same questions, so every call is a hit.

Modes: `use` reads and stores (the default), `refresh` calls again and stores
the new reply, `off` neither reads nor stores. For a fresh sample, change the
seed: the seed is part of the key. Mock agents are never cached.

Identical requests in flight at once (parallel sweep arms often ask the same
first question) share one call, so every run that asked it records the same
reply that a replay will return.
"""

import asyncio
import dataclasses
import hashlib
import json
import sqlite3
from pathlib import Path

from collusion_lab.backends import Reply

MODES = ("use", "refresh", "off")
DEFAULT_PATH = ".cache/responses.sqlite"


class Cache:
    def __init__(self, path=DEFAULT_PATH, mode="use"):
        if mode not in MODES:
            raise ValueError(f"Cache mode must be one of {', '.join(MODES)}.")
        self.path = Path(path)
        self.mode = mode
        self._db = None
        # Calls under way, by key: a second identical request waits for the
        # first instead of making its own call (see CachedBackend).
        self.in_flight = {}

    @staticmethod
    def key(**parts):
        text = json.dumps(parts, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(text.encode()).hexdigest()

    def get(self, key):
        if self.mode != "use":
            return None
        row = (
            self._connect()
            .execute("SELECT reply FROM replies WHERE key = ?", (key,))
            .fetchone()
        )
        return json.loads(row[0]) if row else None

    def observed(self):
        """{(model, reasoning, phase): (mean completion tokens, replies)} over
        every stored reply that records what asked it."""
        if not self.path.exists():
            return {}
        seen = {}
        for (text,) in self._connect().execute("SELECT reply FROM replies"):
            record = json.loads(text)
            about, usage = record.get("about"), record.get("usage")
            if about and usage and usage.get("completion_tokens") is not None:
                where = (about["model"], about["reasoning"], about["phase"])
                seen.setdefault(where, []).append(usage["completion_tokens"])
        return {k: (sum(v) / len(v), len(v)) for k, v in seen.items()}

    def label(self, key, about):
        """Add what asked it to a reply stored before replies recorded that."""
        record = self.get(key)
        record["about"] = about
        self.put(key, record)

    def unlabelled(self):
        """How many stored replies don't say what asked them."""
        if not self.path.exists():
            return 0
        rows = self._connect().execute("SELECT reply FROM replies")
        return sum(1 for (text,) in rows if '"about"' not in text)

    def put(self, key, record):
        if self.mode == "off":
            return
        db = self._connect()
        db.execute(
            "INSERT OR REPLACE INTO replies (key, reply) VALUES (?, ?)",
            (key, json.dumps(record, ensure_ascii=False)),
        )
        db.commit()

    def _connect(self):
        if self._db is None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._db = sqlite3.connect(self.path)
            self._db.execute(
                "CREATE TABLE IF NOT EXISTS replies (key TEXT PRIMARY KEY, reply TEXT)"
            )
        return self._db


def request_key(backend, **asked):
    """A reply's key: the backend's model, address and settings, and what was
    asked (messages, temperature, max_tokens, seed, attempt, agent)."""
    setting = {}
    if (reasoning := getattr(backend, "reasoning", None)) is not None:
        setting["reasoning"] = reasoning
    if getattr(backend, "json_mode", False):
        setting["json_mode"] = True
    if provider := getattr(backend, "provider", None):
        setting["provider"] = provider  # a pinned route; unset adds nothing
    return Cache.key(**setting, model=backend.model, api_base=backend.api_base, **asked)


def backfill_about(path, folders):
    """Label the replies cached at `path` that don't yet say what asked them
    (`about`), by replaying every run under `folders` (each folder with a
    `config.yaml`, full or compact log alike) offline against the cache: a
    cached reply read without `about` gets it then (see `CachedBackend`).
    Only `about` is written, so no key or reply changes. Returns how many
    were labelled."""
    import tempfile

    from collusion_lab.backends import offline
    from collusion_lab.config import load_config
    from collusion_lab.runner import run_sweep

    cache = Cache(path)
    before = cache.unlabelled()
    with tempfile.TemporaryDirectory() as scratch, offline():
        for found in sorted(p for f in folders for p in Path(f).rglob("config.yaml")):
            try:
                config = load_config(found)
            except Exception:  # noqa: BLE001, S112  an old config: skip its run
                continue
            run_sweep(config, Path(scratch) / str(abs(hash(found))), cache)
    return before - cache.unlabelled()


class CachedBackend:
    """Wraps a model backend: answers from the cache, or calls and stores."""

    def __init__(self, inner, cache):
        self.inner = inner
        self.cache = cache

    async def complete(self, messages, *, context, temperature, max_tokens, seed):
        key = request_key(
            self.inner,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            seed=seed,
            attempt=context["attempt"],
            agent=context["me"],
        )
        if hit := self.cache.get(key):
            if hit.pop("about", None) is None and self.cache.mode == "use":
                self.cache.label(key, self._about(context.get("phase")))
            return Reply(**hit, cached=True)
        if self.cache.mode != "off" and key in self.cache.in_flight:
            reply = await self.cache.in_flight[key]
            return dataclasses.replace(
                reply, cached=True, cost=None, seconds=None, retries=None
            )
        ask = self.inner.complete(
            messages,
            context=context,
            temperature=temperature,
            max_tokens=max_tokens,
            seed=seed,
        )
        if self.cache.mode == "off":
            return await ask
        return await self._call_once(key, ask, context.get("phase"))

    def _about(self, phase):
        """What asks this backend's calls: its model, reasoning and phase."""
        reasoning = getattr(self.inner, "reasoning", None)
        return {"model": self.inner.model, "reasoning": reasoning, "phase": phase}

    async def _call_once(self, key, ask, phase):
        """Make the call, sharing it with identical requests that arrive meanwhile."""
        shared = asyncio.get_running_loop().create_future()
        self.cache.in_flight[key] = shared
        try:
            reply = await ask
        except BaseException as error:
            shared.set_exception(error)
            shared.exception()  # mark it seen when nobody else was waiting
            raise
        finally:
            del self.cache.in_flight[key]
        self.cache.put(
            key,
            {
                "text": reply.text,
                "usage": reply.usage,
                "model_version": reply.model_version,
                "reasoning": reply.reasoning,
                "finish_reason": reply.finish_reason,
                "provider": reply.provider,
                "fingerprint": reply.fingerprint,
                "about": self._about(phase),
            },
        )
        shared.set_result(reply)
        return reply


if __name__ == "__main__":
    import sys

    # python -m collusion_lab.cache CACHE RUN_FOLDER ...: label old replies.
    print(f"{backfill_about(sys.argv[1], sys.argv[2:])} replies labelled.")
