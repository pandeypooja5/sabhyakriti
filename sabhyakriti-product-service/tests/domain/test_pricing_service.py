"""Property-based and unit tests for the pricing domain service."""
from __future__ import annotations

from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from domain.services.pricing_service import (
    calculate_discounted_price,
    calculate_savings,
    calculate_stock_status,
)
from domain.value_objects import StockStatus

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

# Valid price: non-negative with up to 2 decimal places
price_strategy = st.decimals(
    min_value=Decimal("0"),
    max_value=Decimal("1000000"),
    allow_nan=False,
    allow_infinity=False,
    places=2,
)

# Valid discount percentage: 0-100 inclusive, up to 2 decimal places
discount_strategy = st.decimals(
    min_value=Decimal("0"),
    max_value=Decimal("100"),
    allow_nan=False,
    allow_infinity=False,
    places=2,
)


# ---------------------------------------------------------------------------
# Property-based tests for calculate_discounted_price
# ---------------------------------------------------------------------------


@given(price=price_strategy, discount_pct=discount_strategy)
@settings(max_examples=500)
def test_discounted_price_never_negative(price: Decimal, discount_pct: Decimal) -> None:
    """Discounted price must always be >= 0."""
    result = calculate_discounted_price(price, discount_pct)
    assert result >= Decimal("0")


@given(price=price_strategy, discount_pct=discount_strategy)
@settings(max_examples=500)
def test_discounted_price_never_exceeds_original(
    price: Decimal, discount_pct: Decimal
) -> None:
    """Discounted price must never exceed original price."""
    result = calculate_discounted_price(price, discount_pct)
    assert result <= price


@given(price=price_strategy, discount_pct=discount_strategy)
@settings(max_examples=500)
def test_discounted_price_two_decimal_places(
    price: Decimal, discount_pct: Decimal
) -> None:
    """Result must have at most 2 decimal places."""
    result = calculate_discounted_price(price, discount_pct)
    assert result == result.quantize(Decimal("0.01"))


# ---------------------------------------------------------------------------
# Boundary / parametric tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "price, discount_pct, expected",
    [
        (Decimal("100.00"), Decimal("0"), Decimal("100.00")),
        (Decimal("100.00"), Decimal("100"), Decimal("0.00")),
        (Decimal("100.00"), Decimal("10"), Decimal("90.00")),
        (Decimal("999.99"), Decimal("33.33"), Decimal("666.69")),
        (Decimal("0.00"), Decimal("50"), Decimal("0.00")),
        (Decimal("1.00"), Decimal("50"), Decimal("0.50")),
        # Rounding: 100 * (1 - 33/100) = 67 exactly
        (Decimal("100.00"), Decimal("33"), Decimal("67.00")),
    ],
)
def test_discounted_price_parametric(
    price: Decimal, discount_pct: Decimal, expected: Decimal
) -> None:
    result = calculate_discounted_price(price, discount_pct)
    assert result == expected, f"Expected {expected}, got {result}"


def test_discounted_price_raises_on_negative_price() -> None:
    with pytest.raises(ValueError, match="negative"):
        calculate_discounted_price(Decimal("-1"), Decimal("10"))


def test_discounted_price_raises_on_discount_over_100() -> None:
    with pytest.raises(ValueError):
        calculate_discounted_price(Decimal("100"), Decimal("101"))


def test_discounted_price_raises_on_negative_discount() -> None:
    with pytest.raises(ValueError):
        calculate_discounted_price(Decimal("100"), Decimal("-1"))


# ---------------------------------------------------------------------------
# Tests for calculate_savings
# ---------------------------------------------------------------------------


@given(price=price_strategy, discount_pct=discount_strategy)
@settings(max_examples=300)
def test_savings_equals_price_minus_discounted(
    price: Decimal, discount_pct: Decimal
) -> None:
    savings = calculate_savings(price, discount_pct)
    discounted = calculate_discounted_price(price, discount_pct)
    # Allow 1 cent tolerance due to independent rounding
    assert abs(savings - (price - discounted)) <= Decimal("0.01")


def test_savings_zero_on_no_discount() -> None:
    assert calculate_savings(Decimal("100"), Decimal("0")) == Decimal("0.00")


def test_savings_equals_price_on_100_pct_discount() -> None:
    assert calculate_savings(Decimal("100.00"), Decimal("100")) == Decimal("100.00")
