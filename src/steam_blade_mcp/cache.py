"""TTL cache with async stampede prevention."""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


@dataclass
class TTLCache:
    """In-memory TTL cache with per-key locks to prevent thundering herd."""

    default_ttl: float = 300.0  # 5 minutes
    _store: dict[str, CacheEntry] = field(default_factory=dict)
    _locks: dict[str, asyncio.Lock] = field(default_factory=dict)

    def get(self, key: str) -> Any | None:
        """Get a cached value if it exists and hasn't expired."""
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.monotonic() > entry.expires_at:
            del self._store[key]
            return None
        return entry.value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        """Store a value with a TTL."""
        expires_at = time.monotonic() + (ttl if ttl is not None else self.default_ttl)
        self._store[key] = CacheEntry(value=value, expires_at=expires_at)

    def invalidate(self, key: str) -> None:
        """Remove a specific key from the cache."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._store.clear()

    def _get_lock(self, key: str) -> asyncio.Lock:
        """Get or create a per-key lock for stampede prevention."""
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    async def get_or_fetch(
        self,
        key: str,
        fetch_fn: Any,
        ttl: float | None = None,
    ) -> Any:
        """Get from cache or fetch with stampede prevention.

        Only one concurrent caller will execute fetch_fn for a given key;
        others wait for the result.
        """
        cached = self.get(key)
        if cached is not None:
            return cached

        lock = self._get_lock(key)
        async with lock:
            # Double-check after acquiring lock
            cached = self.get(key)
            if cached is not None:
                return cached

            value = await fetch_fn()
            self.set(key, value, ttl)
            return value

    def prune(self) -> int:
        """Remove all expired entries. Returns count of pruned entries."""
        now = time.monotonic()
        expired = [k for k, v in self._store.items() if now > v.expires_at]
        for k in expired:
            del self._store[k]
            self._locks.pop(k, None)
        return len(expired)

    @property
    def size(self) -> int:
        return len(self._store)
