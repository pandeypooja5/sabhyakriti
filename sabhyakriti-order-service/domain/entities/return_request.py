"""ReturnRequest and ReturnItem domain entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from domain.value_objects import ReturnStatus


@dataclass
class ReturnItem:
    """
    A single item line within a return request.

    Supports partial returns — quantity may be less than the original
    order item quantity.
    """

    return_item_id: UUID
    return_request_id: UUID
    order_item_id: UUID
    quantity: int
    reason: str


@dataclass
class ReturnRequest:
    """
    Aggregate representing a customer's request to return items from an order.

    Partial returns are supported: the customer selects specific items and
    quantities from the original order.
    """

    return_request_id: UUID
    order_id: UUID
    user_id: str
    status: ReturnStatus
    reason: str
    items: list[ReturnItem] = field(default_factory=list)
    refund_amount: Decimal = Decimal("0.00")
    admin_notes: str | None = None
    processed_by: str | None = None
    processed_at: datetime | None = None
    items_received_at: datetime | None = None
    refund_initiated_at: datetime | None = None
    refunded_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
