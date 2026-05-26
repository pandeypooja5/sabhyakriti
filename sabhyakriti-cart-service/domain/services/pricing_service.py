"""Domain pricing service — pure functions, no I/O, no side effects.

All monetary arithmetic uses Decimal to prevent rounding errors.
Prices are always fetched live from Product Service; no caching.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from domain.entities.coupon import Coupon
from domain.value_objects import CartTotals, CouponType

_GST_RATE = Decimal("0.05")
_SHIPPING = Decimal("0")
_TWO_PLACES = Decimal("0.01")


@dataclass(frozen=True)
class CartItemWithPrice:
    """Transient struct combining CartItem data with live product price."""

    product_id: object  # UUID, kept generic to avoid circular imports
    quantity: int
    discounted_price: Decimal


def calculate_subtotal(items: list[CartItemWithPrice]) -> Decimal:
    """Sum of (quantity × discounted_price) for all items.

    Returns Decimal("0") for an empty cart.
    """
    total = sum(
        (item.discounted_price * item.quantity for item in items),
        Decimal("0"),
    )
    return total.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)


def apply_coupon_discount(
    subtotal: Decimal,
    coupon: Coupon | None,
) -> Decimal:
    """Calculate the discount amount for a given coupon.

    - FLAT:    min(value, subtotal)   — never reduces below zero
    - PERCENT: subtotal × pct / 100  — no cap, can be large
    - None:    0

    Returns the discount amount (always >= 0, always <= subtotal).
    """
    if coupon is None:
        return Decimal("0")

    if coupon.coupon_type == CouponType.FLAT:
        discount = min(coupon.value, subtotal)
    else:  # PERCENT
        discount = (subtotal * coupon.value / Decimal("100")).quantize(
            _TWO_PLACES, rounding=ROUND_HALF_UP
        )

    # Ensure discount never exceeds subtotal (guard for edge cases)
    return min(discount, subtotal).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_gst(
    taxable: Decimal,
    rate: Decimal = _GST_RATE,
) -> Decimal:
    """Compute GST on the taxable amount.

    GST is calculated on (subtotal - discount), i.e., the NET amount
    after coupon is applied. It is shown as a SEPARATE line item,
    not inclusive in the subtotal.
    """
    return (taxable * rate).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_totals(
    items: list[CartItemWithPrice],
    coupon: Coupon | None,
    price_stale: bool = False,
) -> CartTotals:
    """Compute the full CartTotals value object.

    Formula:
        subtotal        = SUM(qty × discounted_price)
        discount_amount = apply_coupon_discount(subtotal, coupon)
        taxable         = subtotal - discount_amount
        gst_amount      = taxable × 0.05
        shipping_charge = 0  (always free)
        total           = subtotal - discount_amount + gst_amount

    Args:
        items: list of CartItemWithPrice (may be empty)
        coupon: applied coupon entity or None
        price_stale: True when Product Service was unreachable (partial failure)

    Returns:
        CartTotals — frozen dataclass with all monetary fields as Decimal
    """
    subtotal = calculate_subtotal(items)
    discount_amount = apply_coupon_discount(subtotal, coupon)
    taxable = subtotal - discount_amount
    gst_amount = calculate_gst(taxable)
    total = (subtotal - discount_amount + gst_amount).quantize(
        _TWO_PLACES, rounding=ROUND_HALF_UP
    )

    return CartTotals(
        subtotal=subtotal,
        discount_amount=discount_amount,
        gst_amount=gst_amount,
        shipping_charge=_SHIPPING,
        total=total,
        coupon_code=coupon.code if coupon else None,
        price_stale=price_stale,
    )
