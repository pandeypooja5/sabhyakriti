"""
Pure domain service functions — no I/O, no dependencies on infrastructure.

These are stateless helpers that encode core business rules.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from domain.entities.order import Order, OrderItem
from domain.entities.return_request import ReturnItem
from domain.value_objects import OrderStatus

# ---------------------------------------------------------------------------
# Return window configuration
# ---------------------------------------------------------------------------
RETURN_WINDOW_DAYS: int = 7

# ---------------------------------------------------------------------------
# Valid order-status transitions (admin / system only)
# ---------------------------------------------------------------------------
_VALID_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.CONFIRMED: {OrderStatus.SHIPPED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
}


def can_cancel(order: Order) -> bool:
    """
    Return True when the order may be cancelled.

    Only PENDING and CONFIRMED orders can be cancelled; once an order
    has been shipped it is no longer cancellable through the normal flow.
    """
    return order.status in (OrderStatus.PENDING, OrderStatus.CONFIRMED)


def can_request_return(
    order: Order,
    now: datetime,
) -> tuple[bool, str]:
    """
    Return (True, "") when the order is eligible for a return request.

    Rules:
    - Order must be in DELIVERED status.
    - Current time must be within RETURN_WINDOW_DAYS of delivered_at.

    Returns (False, reason_string) on any violation.
    """
    if order.status != OrderStatus.DELIVERED:
        return False, f"Order is not in DELIVERED status (current: {order.status})"

    if order.delivered_at is None:
        return False, "Order has no delivery timestamp recorded"

    # Normalise both datetimes to UTC-aware for safe comparison
    delivered_at = order.delivered_at
    if delivered_at.tzinfo is None:
        delivered_at = delivered_at.replace(tzinfo=timezone.utc)
    now_aware = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)

    delta = now_aware - delivered_at
    if delta.days >= RETURN_WINDOW_DAYS:
        return (
            False,
            f"Return window of {RETURN_WINDOW_DAYS} days has passed "
            f"(delivered {delta.days} days ago)",
        )

    return True, ""


def validate_status_transition(
    current: OrderStatus,
    new: OrderStatus,
) -> bool:
    """
    Return True when transitioning from *current* to *new* is permitted.

    Only admin / system flows (CONFIRMED→SHIPPED, SHIPPED→DELIVERED) are
    validated here.  Cancel and return flows use their own guards.
    """
    allowed = _VALID_TRANSITIONS.get(current, set())
    return new in allowed


def calculate_refund_amount(
    order: Order,
    return_items: list[ReturnItem],
    order_items: list[OrderItem],
) -> Decimal:
    """
    Calculate the refund amount for a (partial) return request.

    Strategy:
    1. Compute the gross value of the returned items at discounted price.
    2. Determine the pro-rata fraction of the order those items represent.
    3. Subtract a pro-rata share of the order-level discount.
    4. Add back a pro-rata share of the GST (since GST is on the net value).

    The formula ensures:
    - refund_amount <= order.total_amount
    - pro-rata fraction is always in [0, 1]
    - Decimal arithmetic is used throughout (no float rounding errors).
    """
    # Index order items by order_item_id for O(1) lookup
    item_map: dict[str, OrderItem] = {
        str(oi.order_item_id): oi for oi in order_items
    }

    # Step 1: gross value of returned items (at discounted_price × qty)
    returned_gross = Decimal("0.00")
    for ri in return_items:
        oi = item_map.get(str(ri.order_item_id))
        if oi is None:
            continue
        returned_gross += oi.discounted_price * ri.quantity

    # Subtotal of the whole order (sum of all discounted item totals)
    order_items_subtotal = sum(
        (oi.discounted_price * oi.quantity for oi in order_items),
        Decimal("0.00"),
    )

    if order_items_subtotal == Decimal("0.00"):
        return Decimal("0.00")

    # Step 2: pro-rata fraction
    pro_rata_fraction = (returned_gross / order_items_subtotal).quantize(
        Decimal("0.000001")
    )
    # Clamp to [0, 1] for safety
    pro_rata_fraction = max(Decimal("0"), min(Decimal("1"), pro_rata_fraction))

    # Step 3: pro-rata discount deduction
    pro_rata_discount = (order.discount_amount * pro_rata_fraction).quantize(
        Decimal("0.01")
    )

    # Step 4: pro-rata GST add-back
    total_gst = order.cgst_amount + order.sgst_amount
    pro_rata_gst = (total_gst * pro_rata_fraction).quantize(Decimal("0.01"))

    # Refund = returned gross - pro-rata discount + pro-rata GST
    refund = (returned_gross - pro_rata_discount + pro_rata_gst).quantize(
        Decimal("0.01")
    )

    # Never exceed order total (safety cap)
    refund = min(refund, order.total_amount)
    refund = max(Decimal("0.00"), refund)

    return refund
