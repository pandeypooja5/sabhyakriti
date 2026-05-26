"""Pure domain pricing service functions."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from domain.value_objects import StockStatus

_LOW_STOCK_THRESHOLD = 5
_TWO_PLACES = Decimal("0.01")


def calculate_discounted_price(price: Decimal, discount_pct: Decimal) -> Decimal:
    """Return discounted price rounded to 2 decimal places.

    Args:
        price: Original price (must be >= 0).
        discount_pct: Discount percentage in range [0, 100].

    Returns:
        Final price after applying discount.
    """
    if price < Decimal("0"):
        raise ValueError("Price cannot be negative")
    if not (Decimal("0") <= discount_pct <= Decimal("100")):
        raise ValueError(f"discount_pct must be in [0, 100], got {discount_pct}")
    factor = (Decimal("100") - discount_pct) / Decimal("100")
    return (price * factor).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_stock_status(qty: int, threshold: int = _LOW_STOCK_THRESHOLD) -> StockStatus:
    """Derive stock status from quantity.

    Args:
        qty: Current stock quantity.
        threshold: Threshold below which stock is considered low.

    Returns:
        StockStatus enum value.
    """
    if qty <= 0:
        return StockStatus.OUT_OF_STOCK
    if qty <= threshold:
        return StockStatus.LOW_STOCK
    return StockStatus.IN_STOCK


def calculate_savings(price: Decimal, discount_pct: Decimal) -> Decimal:
    """Return the monetary savings amount.

    Args:
        price: Original price.
        discount_pct: Discount percentage in range [0, 100].

    Returns:
        Savings amount rounded to 2 decimal places.
    """
    discounted = calculate_discounted_price(price, discount_pct)
    return (price - discounted).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)
