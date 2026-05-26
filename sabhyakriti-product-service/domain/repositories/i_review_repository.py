"""Abstract review repository interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities.review import Review


class IReviewRepository(ABC):
    """Port defining review persistence operations."""

    @abstractmethod
    async def list_for_product(
        self, product_id: UUID, *, page: int = 1, page_size: int = 10
    ) -> tuple[list[Review], int]:
        """Return (reviews, total_count) for a product, newest first."""
        ...

    @abstractmethod
    async def get_by_id(self, review_id: UUID) -> Review | None:
        """Fetch a single review by its primary key."""
        ...

    @abstractmethod
    async def get_by_user_and_product(
        self, user_id: UUID, product_id: UUID
    ) -> Review | None:
        """Return an existing review by a user for a product, or None."""
        ...

    @abstractmethod
    async def create(self, review: Review) -> Review:
        """Persist a new review and return the saved entity."""
        ...

    @abstractmethod
    async def delete(self, review_id: UUID) -> None:
        """Remove a review record.

        Raises:
            LookupError: if the review does not exist.
        """
        ...

    @abstractmethod
    async def recalculate_product_stats(self, product_id: UUID) -> None:
        """Recompute and update average_rating and review_count on the product."""
        ...
