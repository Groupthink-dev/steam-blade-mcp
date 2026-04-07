"""Tests for per-host rate limiter."""

import time

import pytest

from steam_blade_mcp.rate_limiter import HostLimiter, RateLimiter


class TestHostLimiter:
    @pytest.mark.asyncio
    async def test_first_request_immediate(self):
        limiter = HostLimiter(min_interval=1.0)
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start
        assert elapsed < 0.1  # first request is immediate

    @pytest.mark.asyncio
    async def test_respects_interval(self):
        limiter = HostLimiter(min_interval=0.1)
        await limiter.acquire()
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start
        assert elapsed >= 0.09  # allow small tolerance


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_uses_correct_interval_for_web_api(self):
        limiter = RateLimiter()
        host_limiter = limiter._get_limiter("api.steampowered.com")
        assert host_limiter.min_interval == 1.0

    @pytest.mark.asyncio
    async def test_uses_correct_interval_for_store(self):
        limiter = RateLimiter()
        host_limiter = limiter._get_limiter("store.steampowered.com")
        assert host_limiter.min_interval == 1.5

    @pytest.mark.asyncio
    async def test_uses_correct_interval_for_community(self):
        limiter = RateLimiter()
        host_limiter = limiter._get_limiter("steamcommunity.com")
        assert host_limiter.min_interval == 3.0

    @pytest.mark.asyncio
    async def test_default_interval_for_unknown_host(self):
        limiter = RateLimiter()
        host_limiter = limiter._get_limiter("unknown.example.com")
        assert host_limiter.min_interval == 1.0

    @pytest.mark.asyncio
    async def test_acquire_extracts_host(self):
        limiter = RateLimiter()
        # Should not raise
        await limiter.acquire("https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/")
        assert "api.steampowered.com" in limiter._hosts
