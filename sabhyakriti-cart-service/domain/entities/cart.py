"""Cart and CartItem domain entities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Cart:
    """Aggregate root representing a user's shopping cart.

    One cart per user. Auto-created on first item add.
    Persists indefinitely until explicitly cleared.
    """

    cart_id: UUID
    user_id: UUID
    applied_coupon_code: str | None
    created_at: datetime
    updated_at: datetime

    def has_coupon(self) -> bool:
        """Return True if a coupon is currently applied."""
        return self.applied_coupon_code is not None


@dataclass
class CartItem:
    """An item within a cart.

    UNIQUE(cart_id, product_id) — adding the same product
    increments quantity rather than creating a duplicate row.

    Constraints:
    - Max 20 distinct products per cart
    - Max quantity 10 per item
    - quantity=0 triggers removal
    """

    cart_item_id: UUID
    cart_id: UUID
    product_id: UUID
    quantity: int
    added_at: datetime

    def __post_init__(self) -> None:
        if self.quantity < 0:
            raise ValueError("quantity cannot be negative")
        if self.quantity > 10:
            raise ValueError("quantity cannot exceed 10 per item")
