"""Abstract category repository interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities.category import Category
from domain.value_objects import CategoryType


class ICategoryRepository(ABC):
    """Port defining category persistence operations."""

    @abstractmethod
    async def list_categories(
        self, *, type: CategoryType | None = None, active_only: bool = True
    ) -> list[Category]:
        """Return all categories, optionally filtered by type."""
        ...

    @abstractmethod
    async def get_by_id(self, category_id: UUID) -> Category | None:
        """Fetch a single category by its primary key."""
        ...

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Category | None:
        """Fetch a single category by its slug."""
        ...

    @abstractmethod
    async def create(self, category: Category) -> Category:
        """Persist a new category and return the saved entity."""
        ...

    @abstractmethod
    async def update(self, category_id: UUID, updates: dict) -> Category:  # type: ignore[type-arg]
        """Apply partial updates and return the updated entity.

        Raises:
            LookupError: if the category does not exist.
        """
        ...

    @abstractmethod
    async def delete(self, category_id: UUID) -> None:
        """Hard-delete a category.

        Raises:
            LookupError: if the category does not exist.
            ValueError: if the category is still associated with active products.
        """
        ...

    @abstractmethod
    async def has_active_products(self, category_id: UUID) -> bool:
        """Return True if any active products are linked to this category."""
        ...

    @abstractmethod
    async def get_categories_for_product(self, product_id: UUID) -> list[Category]:
        """Return all categories linked to a product."""
        ...
