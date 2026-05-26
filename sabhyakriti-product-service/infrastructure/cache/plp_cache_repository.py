"""Redis PLP cache repository implementation."""
from __future__ import annotations

import json
from typing import Any

import structlog
from redis.asyncio import Redis

from domain.repositories.i_plp_cache_repository import IPlpCacheRepository

logger = structlog.get_logger(__name__)

_PLP_KEY_PATTERN = "product_plp:*"
_SCAN_COUNT = 100


class PlpCacheRepository(IPlpCacheRepository):
    """Redis-backed PLP (Product Listing Page) cache using DB 1."""

    def __init__(self, redis: Redis) -> None:  # type: ignore[type-arg]
        self._redis = redis

    async def get(self, key: str) -> Any | None:
        """Fetch a cached JSON value by key.

        Returns:
            Deserialised Python object, or None on cache miss.
        """
        try:
            raw = await self._redis.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as exc:  # noqa: BLE001
            logger.warning("plp_cache_get_error", key=key, error=str(exc))
            return None

    async def set(self, key: str, value: Any, ttl: int) -> None:
        """Serialise *value* as JSON and store with TTL."""
        try:
            serialised = json.dumps(value, default=str)
            await self._redis.setex(key, ttl, serialised)
        except Exception as exc:  # noqa: BLE001
            logger.warning("plp_cache_set_error", key=key, error=str(exc))

    async def invalidate_all(self) -> None:
        """SCAN all keys matching ``product_plp:*``, then DEL them in one batch.

        Collecting all keys before deleting avoids the cursor-drift issue that
        occurs when keys are deleted mid-iteration.
        """
        try:
            cursor: int = 0
            all_keys: list[str] = []
            while True:
                cursor, keys = await self._redis.scan(
                    cursor=cursor, match=_PLP_KEY_PATTERN, count=_SCAN_COUNT
                )
                all_keys.extend(keys)
                if cursor == 0:
                    break

            if all_keys:
                await self._redis.delete(*all_keys)
            logger.debug("plp_cache_invalidated", deleted_keys=len(all_keys))
        except Exception as exc:  # noqa: BLE001
            logger.warning("plp_cache_invalidate_error", error=str(exc))
