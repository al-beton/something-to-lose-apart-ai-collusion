# Implements: reproducibility/response-cache, reproducibility/cache-modes
"""A response cache, so a seeded run can be replayed exactly and for free.

Provider seeds are best-effort (some providers ignore them, and even
temperature 0 isn't guaranteed deterministic), so exact replay comes from
storing replies. A reply is keyed by everything that shaped it: model,
address, messages, temperature, token limit, seed and attempt. Re-running the
same config and seed asks the same questions, so every call is a hit.

Modes: `use` reads and stores (the default), `refresh` calls again and stores
the new reply, `off` neither reads nor stores. For a fresh sample, change the
seed: the seed is part of the key. Mock agents are never cached.
"""

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
        key = Cache.key(
            model=self.inner.model,
            api_base=self.inner.api_base,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            seed=seed,
            attempt=context["attempt"],
        )
        if hit := self.cache.get(key):
            return Reply(**hit, cached=True)
        reply = await self.inner.complete(
            messages,
            context=context,
            temperature=temperature,
            max_tokens=max_tokens,
            seed=seed,
        )
        self.cache.put(
            key,
            {
                "text": reply.text,
                "usage": reply.usage,
                "model_version": reply.model_version,
            },
        )
        return reply
