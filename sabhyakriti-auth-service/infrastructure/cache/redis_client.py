from __future__ import annotations

import redis.asyncio as aioredis


def create_redis_client(redis_url: str) -> aioredis.Redis:
    return aioredis.from_url(redis_url, decode_responses=True)
