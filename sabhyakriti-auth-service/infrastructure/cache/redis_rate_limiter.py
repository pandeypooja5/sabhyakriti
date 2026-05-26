from __future__ import annotations

import time

import redis.asyncio as aioredis

# Sliding-window rate limiter using a Redis sorted set.
# Each member is a unique request timestamp (float as string).
# Score = timestamp so we can prune old entries with ZREMRANGEBYSCORE.

_SLIDING_WINDOW_SCRIPT = """
local key    = KEYS[1]
local now    = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit  = tonumber(ARGV[3])
local cutoff = now - window

redis.call("ZREMRANGEBYSCORE", key, "-inf", cutoff)
local count = redis.call("ZCARD", key)
if count < limit then
    redis.call("ZADD", key, now, now .. "-" .. math.random(1, 1000000))
    redis.call("EXPIRE", key, window)
    return 1
end
redis.call("EXPIRE", key, window)
return 0
"""

_COUNT_SCRIPT = """
local key    = KEYS[1]
local now    = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit  = tonumber(ARGV[3])
local cutoff = now - window

redis.call("ZREMRANGEBYSCORE", key, "-inf", cutoff)
local count = redis.call("ZCARD", key)
local remaining = limit - count
if remaining < 0 then remaining = 0 end
return remaining
"""


class RedisRateLimiter:
    def __init__(self, redis: aioredis.Redis) -> None:
        self._r = redis

    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.time()
        result = await self._r.eval(  # type: ignore[misc]
            _SLIDING_WINDOW_SCRIPT,
            1,
            key,
            now,
            window_seconds,
            limit,
        )
        return bool(result)

    async def get_remaining(self, key: str, limit: int, window_seconds: int) -> int:
        now = time.time()
        result = await self._r.eval(  # type: ignore[misc]
            _COUNT_SCRIPT,
            1,
            key,
            now,
            window_seconds,
            limit,
        )
        return int(result)
