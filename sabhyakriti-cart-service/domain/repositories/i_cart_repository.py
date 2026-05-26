"""Abstract cart repository interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities.cart import Cart, CartItem


class ICartRepository(ABC):
    """Port (interface) for cart persistence operations."""

    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> Cart | None:
        """Return the user's cart or None if it doesn't exist yet."""
        ...

    @abstractmethod
    async def get_or_create(self, user_id: UUID) -> Cart:
        """Return the user's cart, creating one if it does not exist.

        Uses SELECT FOR UPDATE to prevent race conditions when two
        concurrent requests attempt to create the cart simultaneously.
        """
        ...

    @abstractmethod
    async def get_items(self, cart_id: UUID) -> list[CartItem]:
        """Return all items in the cart."""
        ...

    @abstractmethod
    async def add_item(
        self,
        cart_id: UUID,
        product_id: UUID,
        quantity: int,
    ) -> CartItem:
        """Add an item to the cart or increment quantity if it already exists.

        Uses INSERT ... ON CONFLICT (cart_id, product_id) DO UPDATE.
        Raises ValueError if adding would exceed 20 distinct products.
        Raises ValueError if resulting quantity would exceed 10.
        """
        ...

    @abstractmethod
    async def update_item_quantity(
        self,
        cart_item_id: UUID,
        cart_id: UUID,
        quantity: int,
    ) -> CartItem | None:
        """Set the exact quantity for a cart item.

        Returns None if the item was not found.
        Raises ValueError if quantity would exceed 10.
        """
        ...

    @abstractmethod
    async def remove_item(self, cart_item_id: UUID, cart_id: UUID) -> bool:
        """Remove an item from the cart.

        Returns True if an item was deleted, False if it was not found.
        """
        ...

    @abstractmethod
    async def apply_coupon(self, cart_id: UUID, coupon_code: str) -> Cart:
        """Persist the applied coupon code on the cart."""
        ...

    @abstractmethod
    async def remove_coupon(self, cart_id: UUID) -> Cart:
        """Clear the applied coupon from the cart."""
        ...

    @abstractmethod
    async def clear_cart(self, cart_id: UUID) -> None:
        """Delete all items and clear the applied coupon (idempotent).

        Called by Order Service after a successful order placement.
        """
        ...

    @abstractmethod
    async def get_item_count(self, cart_id: UUID) -> int:
        """Return the number of distinct products in the cart."""
        ...
