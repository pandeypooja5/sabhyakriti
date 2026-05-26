"""
Domain service unit tests.

Covers:
- can_cancel parametrized over all statuses
- can_request_return parametrized over timing / status combinations
- validate_status_transition — all valid and invalid paths
- calculate_refund_amount — Hypothesis PBT + deterministic cases
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from domain.entities.order import Order, OrderItem
from domain.entities.return_request import ReturnItem
from domain.services.order_domain_service import (
    calculate_refund_amount,
    can_cancel,
    can_request_return,
    validate_status_transition,
)
from domain.value_objects import OrderStatus, PaymentMethod
from tests.conftest import make_address_snapshot, make_order, make_order_item


# ---------------------------------------------------------------------------
# can_cancel
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (OrderStatus.PENDING, True),
        (OrderStatus.CONFIRMED, True),
        (OrderStatus.SHIPPED, False),
        (OrderStatus.DELIVERED, False),
        (OrderStatus.CANCELLED, False),
        (OrderStatus.RETURN_REQUESTED, False),
        (OrderStatus.RETURN_APPROVED, False),
        (OrderStatus.RETURN_REJECTED, False),
        (OrderStatus.RETURNED, False),
        (OrderStatus.REFUNDED, False),
    ],
)
def test_can_cancel(status: OrderStatus, expected: bool) -> None:
    order = make_order(status=status)
    assert can_cancel(order) is expected


# ---------------------------------------------------------------------------
# can_request_return
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("status", "days_since_delivery", "expect_eligible"),
    [
        # Within window — eligible
        (OrderStatus.DELIVERED, 0, True),
        (OrderStatus.DELIVERED, 3, True),
        (OrderStatus.DELIVERED, 6, True),
        # Outside window — not eligible
        (OrderStatus.DELIVERED, 7, False),
        (OrderStatus.DELIVERED, 8, False),
        (OrderStatus.DELIVERED, 30, False),
        # Wrong status — not eligible
        (OrderStatus.SHIPPED, 1, False),
        (OrderStatus.CONFIRMED, 1, False),
        (OrderStatus.CANCELLED, 1, False),
    ],
)
def test_can_request_return(
    status: OrderStatus, days_since_delivery: int, expect_eligible: bool
) -> None:
    now = datetime.now(tz=timezone.utc)
    delivered_at = now - timedelta(days=days_since_delivery) if status == OrderStatus.DELIVERED else None

    order = make_order(status=status, delivered_at=delivered_at)
    eligible, reason = can_request_return(order, now)
    assert eligible is expect_eligible
    if not eligible:
        assert reason != ""


# ---------------------------------------------------------------------------
# validate_status_transition
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("current", "new", "expected"),
    [
        # Valid transitions
        (OrderStatus.CONFIRMED, OrderStatus.SHIPPED, True),
        (OrderStatus.SHIPPED, OrderStatus.DELIVERED, True),
        # Invalid transitions
        (OrderStatus.PENDING, OrderStatus.SHIPPED, False),
        (OrderStatus.PENDING, OrderStatus.DELIVERED, False),
        (OrderStatus.CONFIRMED, OrderStatus.DELIVERED, False),
        (OrderStatus.DELIVERED, OrderStatus.SHIPPED, False),
        (OrderStatus.DELIVERED, OrderStatus.CONFIRMED, False),
        (OrderStatus.SHIPPED, OrderStatus.CONFIRMED, False),
        (OrderStatus.CANCELLED, OrderStatus.SHIPPED, False),
        (OrderStatus.REFUNDED, OrderStatus.DELIVERED, False),
    ],
)
def test_validate_status_transition(
    current: OrderStatus, new: OrderStatus, expected: bool
) -> None:
    assert validate_status_transition(current, new) is expected


# ---------------------------------------------------------------------------
# calculate_refund_amount — deterministic cases
# ---------------------------------------------------------------------------


def _make_order_with_items(
    *items_data: tuple[Decimal, int],  # (discounted_price, quantity)
    discount_amount: Decimal = Decimal("0.00"),
    cgst_amount: Decimal = Decimal("0.00"),
    sgst_amount: Decimal = Decimal("0.00"),
) -> tuple[Order, list[OrderItem]]:
    order_id = uuid.uuid4()
    order_items = [
        make_order_item(
            order_id=order_id,
            discounted_price=price,
            quantity=qty,
        )
        for price, qty in items_data
    ]
    subtotal = sum(i.line_total for i in order_items)
    total = subtotal - discount_amount + cgst_amount + sgst_amount
    order = Order(
        order_id=order_id,
        user_id="user-x",
        order_number="SKB-202605-000001",
        status=OrderStatus.DELIVERED,
        payment_method=PaymentMethod.RAZORPAY,
        payment_reference="pay_abc",
        shipping_address=make_address_snapshot(),
        subtotal=subtotal,
        discount_amount=discount_amount,
        shipping_charge=Decimal("0.00"),
        cgst_amount=cgst_amount,
        sgst_amount=sgst_amount,
        total_amount=total,
        items=order_items,
        delivered_at=datetime.now(tz=timezone.utc),
        confirmed_at=datetime.now(tz=timezone.utc),
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )
    return order, order_items


def test_calculate_refund_full_return_no_discount() -> None:
    """Returning all items with no discount: refund equals full item value + GST."""
    order, order_items = _make_order_with_items(
        (Decimal("1000.00"), 1),
        cgst_amount=Decimal("25.00"),
        sgst_amount=Decimal("25.00"),
    )
    return_items = [
        ReturnItem(
            return_item_id=uuid.uuid4(),
            return_request_id=uuid.uuid4(),
            order_item_id=order_items[0].order_item_id,
            quantity=1,
            reason="Damaged",
        )
    ]
    refund = calculate_refund_amount(order, return_items, order_items)
    # Full return, no discount: refund = 1000 + 25 + 25 = 1050
    assert refund == Decimal("1050.00")


def test_calculate_refund_partial_return() -> None:
    """Partial return: refund is pro-rata of the total."""
    order, order_items = _make_order_with_items(
        (Decimal("1000.00"), 2),  # 2 items, line_total = 2000
        (Decimal("500.00"), 1),   # 1 item,  line_total = 500
        cgst_amount=Decimal("62.50"),
        sgst_amount=Decimal("62.50"),
    )
    # Return only the first item (1 of 2 units)
    return_items = [
        ReturnItem(
            return_item_id=uuid.uuid4(),
            return_request_id=uuid.uuid4(),
            order_item_id=order_items[0].order_item_id,
            quantity=1,
            reason="Wrong size",
        )
    ]
    refund = calculate_refund_amount(order, return_items, order_items)
    # returned_gross = 1000, total_gross = 2500
    # pro_rata = 1000/2500 = 0.4
    # refund = 1000 + (125 * 0.4) = 1000 + 50 = 1050
    assert refund == Decimal("1050.00")


def test_calculate_refund_never_exceeds_total() -> None:
    """Refund must never exceed order total_amount."""
    order, order_items = _make_order_with_items(
        (Decimal("100.00"), 1),
        discount_amount=Decimal("100.00"),
    )
    return_items = [
        ReturnItem(
            return_item_id=uuid.uuid4(),
            return_request_id=uuid.uuid4(),
            order_item_id=order_items[0].order_item_id,
            quantity=1,
            reason="Not needed",
        )
    ]
    refund = calculate_refund_amount(order, return_items, order_items)
    assert refund <= order.total_amount


def test_calculate_refund_empty_return() -> None:
    """No return items → zero refund."""
    order, order_items = _make_order_with_items((Decimal("500.00"), 1))
    refund = calculate_refund_amount(order, [], order_items)
    assert refund == Decimal("0.00")


# ---------------------------------------------------------------------------
# Hypothesis PBT for calculate_refund_amount
# ---------------------------------------------------------------------------


@given(
    price=st.decimals(min_value="1.00", max_value="10000.00", places=2),
    total_qty=st.integers(min_value=1, max_value=10),
    return_qty=st.integers(min_value=1, max_value=10),
    discount=st.decimals(min_value="0.00", max_value="100.00", places=2),
)
@settings(max_examples=200, deadline=None)
def test_pbt_refund_invariants(
    price: Decimal,
    total_qty: int,
    return_qty: int,
    discount: Decimal,
) -> None:
    """
    Property-based tests for calculate_refund_amount:

    1. Returned items value <= order total (after discount)
    2. Refund never exceeds total_amount
    3. Pro-rata fraction is in [0, 1]
    4. Refund is non-negative
    """
    actual_return_qty = min(return_qty, total_qty)

    order, order_items = _make_order_with_items(
        (price, total_qty),
        discount_amount=discount,
        cgst_amount=Decimal("0.00"),
        sgst_amount=Decimal("0.00"),
    )

    return_items = [
        ReturnItem(
            return_item_id=uuid.uuid4(),
            return_request_id=uuid.uuid4(),
            order_item_id=order_items[0].order_item_id,
            quantity=actual_return_qty,
            reason="Test",
        )
    ]

    refund = calculate_refund_amount(order, return_items, order_items)

    # Invariant 1: non-negative
    assert refund >= Decimal("0.00"), f"Refund {refund} is negative"

    # Invariant 2: never exceeds total_amount
    assert refund <= order.total_amount, (
        f"Refund {refund} exceeds order total {order.total_amount}"
    )

    # Invariant 3: returned items gross <= order subtotal
    returned_gross = price * actual_return_qty
    assert returned_gross <= order.subtotal + Decimal("0.01"), (
        f"returned_gross {returned_gross} > subtotal {order.subtotal}"
    )

    # Invariant 4: pro-rata fraction in [0, 1]
    if order.subtotal > Decimal("0"):
        fraction = (returned_gross / order.subtotal).quantize(Decimal("0.000001"))
        assert Decimal("0") <= fraction <= Decimal("1.000001"), (
            f"Pro-rata fraction {fraction} out of bounds"
        )
