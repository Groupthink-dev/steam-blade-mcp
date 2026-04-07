"""Per-host async rate limiter."""

import asyncio
import time
from dataclasses import dataclass, field


@dataclass
class HostLimiter:
    """Rate limiter for a single host."""

    min_interval: float  # minimum seconds between requests
    _last_request: float = 0.0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def acquire(self) -> None:
        """Wait until we can make a request, respecting the rate limit."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)
            self._last_request = time.monotonic()


@dataclass
class RateLimiter:
    """Per-host rate limiter.

    Default intervals:
    - Steam Web API: 1.0s (safe for ~100K/day)
    - Steam Store API: 1.5s (stricter, ~200/5min)
    - Steam Community: 3.0s (very strict, IP-based)
    """

    _hosts: dict[str, HostLimiter] = field(default_factory=dict)

    # Default intervals per host pattern
    HOST_INTERVALS: dict[str, float] = field(
        default_factory=lambda: {
            "api.steampowered.com": 1.0,
            "store.steampowered.com": 1.5,
            "steamcommunity.com": 3.0,
        }
    )

    def _get_limiter(self, host: str) -> HostLimiter:
        if host not in self._hosts:
            interval = self.HOST_INTERVALS.get(host, 1.0)
            self._hosts[host] = HostLimiter(min_interval=interval)
        return self._hosts[host]

    async def acquire(self, url: str) -> None:
        """Acquire a rate limit slot for the given URL's host."""
        # Extract host from URL
        from urllib.parse import urlparse

        parsed = urlparse(url)
        host = parsed.hostname or ""
        limiter = self._get_limiter(host)
        await limiter.acquire()
