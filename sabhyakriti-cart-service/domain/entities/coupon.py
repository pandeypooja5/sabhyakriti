"""Coupon domain entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from domain.value_objects import CouponType


@dataclass
class Coupon:
    """Represents a discount coupon.

    Supports two types:
    - FLAT: min(value, subtotal) — flat amount discount, never exceeds subtotal
    - PERCENT: subtotal × pct / 100 — no cap, can be large
    """

    coupon_id: UUID
    code: str  # Always stored/compared uppercase
    coupon_type: CouponType
    value: Decimal  # flat amount or percentage
    min_order_amount: Decimal
    max_uses: int | None  # None = unlimited
    used_count: int
    is_active: bool
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime

    def is_valid(self, now: datetime, subtotal: Decimal) -> tuple[bool, str]:
        """Validate coupon against current time and cart subtotal.

        Returns:
            (True, "") if valid
            (False, error_message) if invalid
        """
        if not self.is_active:
            return False, "Coupon is not active."

        if self.expires_at is not None and now > self.expires_at:
            return False, "Coupon has expired."

        if (
            self.max_uses is not None
            and self.used_count >= self.max_uses
        ):
            return False, "Coupon usage limit has been reached."

        if subtotal < self.min_order_amount:
            return (
                False,
                f"Minimum order amount of ₹{self.min_order_amount} required.",
            )

        return True, ""
