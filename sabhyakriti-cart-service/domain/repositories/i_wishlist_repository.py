"""Abstract wishlist repository interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities.wishlist import Wishlist, WishlistItem


class IWishlistRepository(ABC):
    """Port (interface) for wishlist persistence operations."""

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> Wishlist | None:
        """Return the user's wishlist or None if it doesn't exist yet."""
        ...

    @abstractmethod
    async def get_or_create(self, user_id: UUID) -> Wishlist:
        """Return the user's wishlist, creating one if it does not exist."""
        ...

    @abstractmethod
    async def get_items(self, wishlist_id: UUID) -> list[WishlistItem]:
        """Return all items in the wishlist."""
        ...

    @abstractmethod
    async def add_item(
        self,
        wishlist_id: UUID,
        product_id: UUID,
    ) -> WishlistItem:
        """Add a product to the wishlist.

        Uses INSERT ON CONFLICT DO NOTHING — idempotent operation.
        Returns the existing or newly created WishlistItem.
        """
        ...

    @abstractmethod
    async def remove_item(
        self,
        wishlist_id: UUID,
        product_id: UUID,
    ) -> bool:
        """Remove a product from the wishlist.

        Returns True if removed, False if not found.
        """
        ...
