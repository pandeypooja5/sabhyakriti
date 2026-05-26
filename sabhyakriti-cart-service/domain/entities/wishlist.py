"""Wishlist and WishlistItem domain entities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Wishlist:
    """Aggregate root representing a user's wishlist.

    One wishlist per user. Auto-created on first item add.
    """

    wishlist_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


@dataclass
class WishlistItem:
    """An item within a wishlist.

    UNIQUE(wishlist_id, product_id) — adding the same product is idempotent.
    """

    wishlist_item_id: UUID
    wishlist_id: UUID
    product_id: UUID
    added_at: datetime
