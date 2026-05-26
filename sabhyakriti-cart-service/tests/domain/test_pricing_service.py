"""Property-based tests for the domain pricing service using Hypothesis."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from uuid import uuid4

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from domain.entities.coupon import Coupon
from domain.services.pricing_service import (
    CartItemWithPrice,
    apply_coupon_discount,
    calculate_gst,
    calculate_subtotal,
    calculate_totals,
)
from domain.value_objects import CartTotals, CouponType
from tests.conftest import make_coupon

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

_price_strategy = st.decimals(
    min_value=Decimal("0.01"),
    max_value=Decimal("99999.99"),
    places=2,
    allow_nan=False,
    allow_infinity=False,
)

_qty_strategy = st.integers(min_value=1, max_value=10)

_item_strategy = st.builds(
    CartItemWithPrice,
    product_id=st.just(uuid4()),
    quantity=_qty_strategy,
    discounted_price=_price_strategy,
)

_items_strategy = st.lists(_item_strategy, min_size=0, max_size=20)

_flat_coupon_strategy = st.builds(
    make_coupon,
    coupon_type=st.just(CouponType.FLAT),
    value=_price_strategy,
    min_order_amount=st.just(Decimal("0")),
    max_uses=st.none(),
    used_count=st.just(0),
    is_active=st.just(True),
    expires_at=st.none(),
)

_percent_coupon_strategy = st.builds(
    make_coupon,
    coupon_type=st.just(CouponType.PERCENT),
    value=st.decimals(
        min_value=Decimal("1"),
        max_value=Decimal("100"),
        places=2,
        allow_nan=False,
        allow_infinity=False,
    ),
    min_order_amount=st.just(Decimal("0")),
    max_uses=st.none(),
    used_count=st.just(0),
    is_active=st.just(True),
    expires_at=st.none(),
)


# ---------------------------------------------------------------------------
# Property: total == subtotal - discount + gst (the fundamental invariant)
# ---------------------------------------------------------------------------

@given(items=_items_strategy, coupon=st.one_of(st.none(), _flat_coupon_strategy))
@settings(max_examples=200)
def test_total_equals_subtotal_minus_discount_plus_gst(
    items: list[CartItemWithPrice],
    coupon: Coupon | None,
) -> None:
    """PROPERTY: total = subtotal - discount_amount + gst_amount always."""
    totals = calculate_totals(items, coupon)
    expected = (totals.subtotal - totals.discount_amount + totals.gst_amount).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    assert totals.total == expected, (
        f"total={totals.total} != expected={expected}"
    )


# ---------------------------------------------------------------------------
# Property: GST is always exactly 5% of the taxable amount
# ---------------------------------------------------------------------------

@given(
    items=_items_strategy,
    coupon=st.one_of(st.none(), _flat_coupon_strategy, _percent_coupon_strategy),
)
@settings(max_examples=200)
def test_gst_is_five_percent_of_taxable_amount(
    items: list[CartItemWithPrice],
    coupon: Coupon | None,
) -> None:
    """PROPERTY: gst_amount = 5% of (subtotal - discount) rounded to 2dp."""
    totals = calculate_totals(items, coupon)
    taxable = totals.subtotal - totals.discount_amount
    expected_gst = (taxable * Decimal("0.05")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    assert totals.gst_amount == expected_gst


# ---------------------------------------------------------------------------
# Property: Shipping is always zero
# ---------------------------------------------------------------------------

@given(items=_items_strategy, coupon=st.one_of(st.none(), _flat_coupon_strategy))
@settings(max_examples=100)
def test_shipping_always_zero(
    items: list[CartItemWithPrice],
    coupon: Coupon | None,
) -> None:
    """PROPERTY: shipping_charge is always ₹0."""
    totals = calculate_totals(items, coupon)
    assert totals.shipping_charge == Decimal("0")


# ---------------------------------------------------------------------------
# Property: FLAT coupon discount never exceeds subtotal
# ---------------------------------------------------------------------------

@given(items=_items_strategy, coupon=_flat_coupon_strategy)
@settings(max_examples=200)
def test_flat_coupon_never_exceeds_subtotal(
    items: list[CartItemWithPrice],
    coupon: Coupon,
) -> None:
    """PROPERTY: FLAT discount <= subtotal (cart never goes negative)."""
    subtotal = calculate_subtotal(items)
    discount = apply_coupon_discount(subtotal, coupon)
    assert discount <= subtotal


# ---------------------------------------------------------------------------
# Property: PERCENT coupon has no cap (can be large on high values)
# ---------------------------------------------------------------------------

@given(coupon=_percent_coupon_strategy)
@settings(max_examples=100)
def test_percent_coupon_no_cap(coupon: Coupon) -> None:
    """PROPERTY: PERCENT coupon is computed as subtotal × pct/100, no hard cap."""
    subtotal = Decimal("10000.00")
    discount = apply_coupon_discount(subtotal, coupon)
    expected = (subtotal * coupon.value / Decimal("100")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    assert discount == min(expected, subtotal)


# ---------------------------------------------------------------------------
# Property: GST is calculated on NET amount (after discount, not gross)
# ---------------------------------------------------------------------------

@given(
    items=_items_strategy,
    coupon=_flat_coupon_strategy,
)
@settings(max_examples=200)
def test_gst_calculated_on_net_not_gross(
    items: list[CartItemWithPrice],
    coupon: Coupon,
) -> None:
    """PROPERTY: GST is on (subtotal - discount), not raw subtotal."""
    totals_with = calculate_totals(items, coupon)
    totals_without = calculate_totals(items, None)

    # If there is a discount, GST with coupon should be <= GST without
    if totals_with.discount_amount > Decimal("0"):
        assert totals_with.gst_amount <= totals_without.gst_amount


# ---------------------------------------------------------------------------
# Unit tests for specific values
# ---------------------------------------------------------------------------

def test_empty_cart_totals() -> None:
    """Empty cart has all-zero totals."""
    totals = calculate_totals([], None)
    assert totals.subtotal == Decimal("0")
    assert totals.discount_amount == Decimal("0")
    assert totals.gst_amount == Decimal("0")
    assert totals.total == Decimal("0")
    assert totals.shipping_charge == Decimal("0")
    assert totals.coupon_code is None


def test_subtotal_calculation() -> None:
    """Subtotal = sum of qty × price."""
    items = [
        CartItemWithPrice(product_id=uuid4(), quantity=2, discounted_price=Decimal("500")),
        CartItemWithPrice(product_id=uuid4(), quantity=1, discounted_price=Decimal("300")),
    ]
    assert calculate_subtotal(items) == Decimal("1300.00")


def test_flat_coupon_reduces_by_value() -> None:
    """FLAT coupon deducts fixed amount."""
    coupon = make_coupon(coupon_type=CouponType.FLAT, value=Decimal("200"))
    discount = apply_coupon_discount(Decimal("1000"), coupon)
    assert discount == Decimal("200.00")


def test_flat_coupon_capped_at_subtotal() -> None:
    """FLAT coupon capped at subtotal when value > subtotal."""
    coupon = make_coupon(coupon_type=CouponType.FLAT, value=Decimal("500"))
    discount = apply_coupon_discount(Decimal("300"), coupon)
    assert discount == Decimal("300.00")


def test_percent_coupon_calculation() -> None:
    """PERCENT coupon = subtotal × pct / 100."""
    coupon = make_coupon(coupon_type=CouponType.PERCENT, value=Decimal("10"))
    discount = apply_coupon_discount(Decimal("1000"), coupon)
    assert discount == Decimal("100.00")


def test_calculate_gst_five_percent() -> None:
    """GST = 5% of taxable amount."""
    gst = calculate_gst(Decimal("1000"))
    assert gst == Decimal("50.00")


def test_full_totals_with_flat_coupon() -> None:
    """Integration: full totals with a FLAT coupon."""
    items = [
        CartItemWithPrice(
            product_id=uuid4(), quantity=2, discounted_price=Decimal("1000")
        )
    ]
    coupon = make_coupon(coupon_type=CouponType.FLAT, value=Decimal("200"))
    totals = calculate_totals(items, coupon)

    assert totals.subtotal == Decimal("2000.00")
    assert totals.discount_amount == Decimal("200.00")
    assert totals.gst_amount == Decimal("90.00")   # 5% of 1800
    assert totals.total == Decimal("1890.00")
    assert totals.shipping_charge == Decimal("0")
    assert totals.coupon_code == coupon.code


def test_price_stale_flag_propagated() -> None:
    """price_stale flag is passed through to CartTotals."""
    totals = calculate_totals([], None, price_stale=True)
    assert totals.price_stale is True
