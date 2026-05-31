"""Abstract product repository interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from domain.entities.product import Product
from domain.value_objects import SortOrder


class IProductRepository(ABC):
    """Port defining product persistence operations."""

    @abstractmethod
    async def list_products(
        self,
        *,
        fabric_ids: list[UUID] | None = None,
        occasion_ids: list[UUID] | None = None,
        region_ids: list[UUID] | None = None,
        search: str | None = None,
        sort: SortOrder = SortOrder.NEWEST,
        page: int = 1,
        page_size: int = 24,
    ) -> tuple[list[Product], int]:
        """Return (products, total_count) matching the given filters."""
        ...

    @abstractmethod
    async def get_by_id(self, product_id: UUID) -> Product | None:
        """Fetch a single active product by its primary key."""
        ...

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Product | None:
        """Fetch a single active product by its URL slug."""
        ...

    @abstractmethod
    async def find_by_ids(self, product_ids: list[UUID]) -> list[Product]:
        """Fetch multiple active products by their IDs."""
        ...

    @abstractmethod
    async def get_slug_set(self) -> set[str]:
        """Return all existing slugs (used during slug uniqueness check)."""
        ...

    @abstractmethod
    async def create(self, product: Product) -> Product:
        """Persist a new product and return the saved entity."""
        ...

    @abstractmethod
    async def update(self, product_id: UUID, updates: dict[str, Any]) -> Product:
        """Apply partial updates and return the updated entity.

        Raises:
            LookupError: if the product does not exist.
        """
        ...

    @abstractmethod
    async def soft_delete(self, product_id: UUID) -> None:
        """Mark a product as inactive (is_active=False).

        Raises:
            LookupError: if the product does not exist.
        """
        ...

    @abstractmethod
    async def reserve_stock(self, product_id: UUID, delta: int) -> Product:
        """Decrement stock_qty by *delta* atomically.

        Uses row-level locking to ensure the decrement only happens when
        ``stock_qty >= delta``.

        Returns:
            Updated product.

        Raises:
            LookupError: If the product does not exist.
            ValueError: If insufficient stock (0 rows updated).
        """
        ...

    @abstractmethod
    async def release_stock(self, product_id: UUID, delta: int) -> Product:
        """Increment stock_qty by *delta* atomically.

        Raises:
            LookupError: If the product does not exist.
        """
        ...

    @abstractmethod
    async def get_related_products(
        self, product_id: UUID, limit: int = 6
    ) -> list[Product]:
        """Return products sharing at least one category with *product_id*."""
        ...

    @abstractmethod
    async def slug_exists(self, slug: str) -> bool:
        """Check whether a slug is already taken."""
        ...
