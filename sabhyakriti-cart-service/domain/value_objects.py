"""Domain value objects for the cart service."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum


class CouponType(StrEnum):
    """Coupon discount type."""

    FLAT = "FLAT"
    PERCENT = "PERCENT"


@dataclass(frozen=True)
class CartTotals:
    """Immutable value object representing cart pricing totals.

    All monetary values use Decimal to avoid floating-point rounding errors.
    GST is shown as a separate line item (not inclusive in subtotal).
    Shipping is always ₹0 for this platform.
    """

    subtotal: Decimal
    discount_amount: Decimal
    gst_amount: Decimal
    shipping_charge: Decimal
    total: Decimal
    coupon_code: str | None = None
    price_stale: bool = False

    def __post_init__(self) -> None:
        """Validate invariants."""
        if self.subtotal < Decimal("0"):
            raise ValueError("subtotal cannot be negative")
        if self.discount_amount < Decimal("0"):
            raise ValueError("discount_amount cannot be negative")
        if self.gst_amount < Decimal("0"):
            raise ValueError("gst_amount cannot be negative")
        if self.shipping_charge != Decimal("0"):
            raise ValueError("shipping_charge must be 0")
        expected_total = self.subtotal - self.discount_amount + self.gst_amount
        if self.total != expected_total:
            raise ValueError(
                f"total ({self.total}) != subtotal - discount + gst "
                f"({expected_total})"
            )
