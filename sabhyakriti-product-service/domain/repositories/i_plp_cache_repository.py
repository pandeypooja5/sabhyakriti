"""Abstract PLP (Product Listing Page) cache repository interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IPlpCacheRepository(ABC):
    """Port defining PLP Redis cache operations."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Fetch a cached value by key.

        Returns:
            Deserialised value, or None on cache miss.
        """
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int) -> None:
        """Store *value* under *key* with a TTL in seconds."""
        ...

    @abstractmethod
    async def invalidate_all(self) -> None:
        """Remove all keys matching the pattern ``product_plp:*``."""
        ...
