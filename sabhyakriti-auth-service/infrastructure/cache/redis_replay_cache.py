from __future__ import annotations

import redis.asyncio as aioredis


class RedisReplayCache:
    """Implements IReplayCache for MFA TOTP replay prevention."""

    def __init__(self, redis: aioredis.Redis) -> None:
        self._r = redis

    async def is_used(self, key: str) -> bool:
        return bool(await self._r.exists(key))

    async def mark_used(self, key: str, ttl_seconds: int) -> None:
        await self._r.setex(key, ttl_seconds, "1")
