# Implements: backends/reasoning-in-estimate, reproducibility/response-cache, reproducibility/cache-modes, logs/reasoning-logged, agents/json-mode
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


class CachedBackend:
    """Wraps a model backend: answers from the cache, or calls and stores."""

    def __init__(self, inner, cache):
        self.inner = inner
        self.cache = cache

    async def complete(self, messages, *, context, temperature, max_tokens, seed):
        setting = {}
        if (reasoning := getattr(self.inner, "reasoning", None)) is not None:
            setting["reasoning"] = reasoning
        if getattr(self.inner, "json_mode", False):
            setting["json_mode"] = True
        key = Cache.key(
            **setting,
            model=self.inner.model,
            api_base=self.inner.api_base,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            seed=seed,
            attempt=context["attempt"],
            agent=context["me"],
        )
        if hit := self.cache.get(key):
            hit.pop("about", None)
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
                "about": {
                    "model": self.inner.model,
                    "reasoning": getattr(self.inner, "reasoning", None),
                    "phase": phase,
                },
            },
        )
        shared.set_result(reply)
        return reply
