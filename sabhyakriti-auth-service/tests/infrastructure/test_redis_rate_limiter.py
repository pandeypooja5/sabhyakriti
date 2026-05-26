from __future__ import annotations

import fakeredis.aioredis
import pytest
import pytest_asyncio
from hypothesis import given, settings, strategies as st

from infrastructure.cache.redis_rate_limiter import RedisRateLimiter


@pytest_asyncio.fixture
async def limiter():
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield RedisRateLimiter(r)
    await r.aclose()


@pytest.mark.asyncio
async def test_allows_within_limit(limiter: RedisRateLimiter) -> None:
    for _ in range(5):
        assert await limiter.is_allowed("test:ip1", limit=5, window_seconds=60)


@pytest.mark.asyncio
async def test_blocks_at_limit(limiter: RedisRateLimiter) -> None:
    for _ in range(5):
        await limiter.is_allowed("test:ip2", limit=5, window_seconds=60)
    blocked = await limiter.is_allowed("test:ip2", limit=5, window_seconds=60)
    assert not blocked


@pytest.mark.asyncio
async def test_different_keys_independent(limiter: RedisRateLimiter) -> None:
    for _ in range(5):
        await limiter.is_allowed("key_a", limit=5, window_seconds=60)
    # key_a is at limit, key_b should still be allowed
    assert await limiter.is_allowed("key_b", limit=5, window_seconds=60)
