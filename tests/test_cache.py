"""Tests for TTL cache with stampede prevention."""

import asyncio
import time

import pytest

from steam_blade_mcp.cache import TTLCache


class TestTTLCache:
    def test_get_miss(self):
        cache = TTLCache()
        assert cache.get("nonexistent") is None

    def test_set_and_get(self):
        cache = TTLCache()
        cache.set("key", "value")
        assert cache.get("key") == "value"

    def test_expiry(self):
        cache = TTLCache()
        cache.set("key", "value", ttl=0.01)
        time.sleep(0.02)
        assert cache.get("key") is None

    def test_invalidate(self):
        cache = TTLCache()
        cache.set("key", "value")
        cache.invalidate("key")
        assert cache.get("key") is None

    def test_invalidate_nonexistent(self):
        cache = TTLCache()
        cache.invalidate("nonexistent")  # no error

    def test_clear(self):
        cache = TTLCache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.size == 0

    def test_size(self):
        cache = TTLCache()
        assert cache.size == 0
        cache.set("a", 1)
        assert cache.size == 1
        cache.set("b", 2)
        assert cache.size == 2

    def test_prune(self):
        cache = TTLCache()
        cache.set("expire", "yes", ttl=0.01)
        cache.set("keep", "yes", ttl=100)
        time.sleep(0.02)
        pruned = cache.prune()
        assert pruned == 1
        assert cache.size == 1
        assert cache.get("keep") == "yes"


class TestGetOrFetch:
    @pytest.mark.asyncio
    async def test_fetches_on_miss(self):
        cache = TTLCache()
        call_count = 0

        async def fetch():
            nonlocal call_count
            call_count += 1
            return "fetched"

        result = await cache.get_or_fetch("key", fetch)
        assert result == "fetched"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_returns_cached(self):
        cache = TTLCache()
        cache.set("key", "cached")
        call_count = 0

        async def fetch():
            nonlocal call_count
            call_count += 1
            return "fetched"

        result = await cache.get_or_fetch("key", fetch)
        assert result == "cached"
        assert call_count == 0

    @pytest.mark.asyncio
    async def test_stampede_prevention(self):
        """Multiple concurrent fetches for the same key should only call fetch once."""
        cache = TTLCache()
        call_count = 0

        async def slow_fetch():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.05)
            return f"result-{call_count}"

        # Launch 5 concurrent fetches
        results = await asyncio.gather(
            cache.get_or_fetch("key", slow_fetch),
            cache.get_or_fetch("key", slow_fetch),
            cache.get_or_fetch("key", slow_fetch),
            cache.get_or_fetch("key", slow_fetch),
            cache.get_or_fetch("key", slow_fetch),
        )

        # Only one fetch should have executed
        assert call_count == 1
        # All results should be the same
        assert all(r == "result-1" for r in results)

    @pytest.mark.asyncio
    async def test_custom_ttl(self):
        cache = TTLCache()

        async def fetch():
            return "value"

        await cache.get_or_fetch("key", fetch, ttl=0.01)
        assert cache.get("key") == "value"
        await asyncio.sleep(0.02)
        assert cache.get("key") is None
