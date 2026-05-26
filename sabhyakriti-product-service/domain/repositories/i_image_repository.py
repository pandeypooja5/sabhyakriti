"""Abstract image repository interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities.product import ProductImage


class IImageRepository(ABC):
    """Port defining product image persistence operations."""

    @abstractmethod
    async def list_for_product(self, product_id: UUID) -> list[ProductImage]:
        """Return all images for a product ordered by sort_order."""
        ...

    @abstractmethod
    async def get_by_id(self, image_id: UUID) -> ProductImage | None:
        """Fetch a single image by its primary key."""
        ...

    @abstractmethod
    async def count_for_product(self, product_id: UUID) -> int:
        """Return the number of images for a product."""
        ...

    @abstractmethod
    async def create(self, image: ProductImage) -> ProductImage:
        """Persist a new product image and return the saved entity."""
        ...

    @abstractmethod
    async def clear_primary_flag(self, product_id: UUID) -> None:
        """Set is_primary=False on all images for a product."""
        ...

    @abstractmethod
    async def set_primary(self, image_id: UUID) -> None:
        """Set is_primary=True on a specific image.

        Raises:
            LookupError: if the image does not exist.
        """
        ...

    @abstractmethod
    async def delete(self, image_id: UUID) -> None:
        """Remove an image record.

        Raises:
            LookupError: if the image does not exist.
        """
        ...

    @abstractmethod
    async def promote_first_as_primary(self, product_id: UUID) -> None:
        """Set the lowest-sort_order image as primary if no primary exists."""
        ...
