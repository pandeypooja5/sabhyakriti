"""Tests for PlpCacheRepository using fakeredis."""
from __future__ import annotations

import asyncio

import fakeredis.aioredis
import pytest

from infrastructure.cache.plp_cache_repository import PlpCacheRepository


@pytest.fixture
async def redis():
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield r
    await r.aclose()


@pytest.fixture
def cache(redis):
    return PlpCacheRepository(redis)


# ---------------------------------------------------------------------------
# set / get tests
# ---------------------------------------------------------------------------


async def test_set_and_get_returns_value(cache):
    """set followed by get returns the same value."""
    await cache.set("product_plp:abc123", {"items": [], "total": 0}, ttl=300)
    result = await cache.get("product_plp:abc123")
    assert result == {"items": [], "total": 0}


async def test_get_missing_key_returns_none(cache):
    """get on a non-existent key returns None."""
    result = await cache.get("product_plp:nonexistent")
    assert result is None


async def test_set_serialises_complex_types(cache):
    """JSON serialisation handles nested dicts/lists."""
    value = {
        "items": [
            {"product_id": "uuid-1", "name": "Silk Saree", "price": "5000.00"}
        ],
        "total_count": 1,
        "page": 1,
        "total_pages": 1,
    }
    await cache.set("product_plp:complex", value, ttl=60)
    result = await cache.get("product_plp:complex")
    assert result == value


async def test_ttl_is_set(cache, redis):
    """Stored key should have a positive TTL."""
    key = "product_plp:ttltest"
    await cache.set(key, {"data": "test"}, ttl=300)
    ttl = await redis.ttl(key)
    assert ttl > 0
    assert ttl <= 300


# ---------------------------------------------------------------------------
# invalidate_all tests
# ---------------------------------------------------------------------------


async def test_invalidate_all_removes_plp_keys(cache, redis):
    """invalidate_all must delete all product_plp:* keys."""
    await cache.set("product_plp:key1", {"a": 1}, ttl=300)
    await cache.set("product_plp:key2", {"b": 2}, ttl=300)
    await cache.set("product_plp:key3", {"c": 3}, ttl=300)

    await cache.invalidate_all()

    remaining_keys = await redis.keys("product_plp:*")
    assert remaining_keys == []


async def test_invalidate_all_does_not_remove_other_keys(cache, redis):
    """invalidate_all must NOT remove keys that don't match product_plp:*."""
    await cache.set("product_plp:key1", {"a": 1}, ttl=300)
    await redis.setex("other_service:key1", 300, "some_value")
    await redis.setex("product_detail:xyz", 300, "detail_value")

    await cache.invalidate_all()

    # PLP keys gone
    plp_keys = await redis.keys("product_plp:*")
    assert plp_keys == []

    # Other keys intact
    assert await redis.get("other_service:key1") == "some_value"
    assert await redis.get("product_detail:xyz") == "detail_value"


async def test_invalidate_all_on_empty_cache_is_safe(cache):
    """Calling invalidate_all when no keys exist should not raise."""
    await cache.invalidate_all()  # Must not raise


async def test_invalidate_all_clears_many_keys(cache, redis):
    """invalidate_all must handle > SCAN_COUNT keys."""
    for i in range(150):
        await redis.setex(f"product_plp:key{i}", 300, f"val{i}")

    all_keys_before = await redis.keys("product_plp:*")
    assert len(all_keys_before) == 150

    await cache.invalidate_all()

    all_keys_after = await redis.keys("product_plp:*")
    assert len(all_keys_after) == 0


# ---------------------------------------------------------------------------
# Error resilience
# ---------------------------------------------------------------------------


async def test_get_returns_none_on_malformed_json(cache, redis):
    """Malformed JSON in cache should return None rather than raise."""
    await redis.setex("product_plp:bad_json", 300, "{ not valid json !!!}")
    result = await cache.get("product_plp:bad_json")
    assert result is None
