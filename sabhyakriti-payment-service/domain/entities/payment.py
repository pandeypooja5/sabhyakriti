"""Domain entities for the payment bounded context."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from domain.value_objects import PaymentMethod, PaymentStatus


@dataclass
class Payment:
    """Core payment aggregate root.

    Tracks the full lifecycle of a payment from creation through
    capture, failure, cancellation or refund.
    """

    payment_id: UUID
    order_id: UUID
    user_id: UUID
    amount: Decimal
    currency: str
    method: PaymentMethod
    status: PaymentStatus

    # Razorpay-specific identifiers
    razorpay_order_id: str | None = None
    razorpay_payment_id: str | None = None
    razorpay_signature: str | None = None

    # Attempt tracking for rate-limiting (max 3 per 30-minute window)
    attempt_count: int = 0
    first_attempt_at: datetime | None = None

    # Capture details
    captured_at: datetime | None = None

    # Refund details
    refund_id: str | None = None
    refund_amount: Decimal | None = None
    refunded_at: datetime | None = None

    # Audit fields
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def is_capturable(self) -> bool:
        """Return True if the payment can transition to CAPTURED."""
        return self.status == PaymentStatus.CREATED

    def is_refundable(self) -> bool:
        """Return True if the payment can be refunded."""
        return self.status == PaymentStatus.CAPTURED and self.refund_id is None

    def is_cancellable(self) -> bool:
        """Return True if the payment can be cancelled."""
        return self.status == PaymentStatus.CREATED


@dataclass
class WebhookEvent:
    """Represents an incoming Razorpay webhook event.

    The ``razorpay_event_id`` is used as an idempotency key — duplicate
    events with the same ID are silently ignored via a UNIQUE constraint.
    """

    event_id: UUID
    razorpay_event_id: str
    event_type: str
    payload: dict  # type: ignore[type-arg]
    processed: bool = False
    error_message: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: datetime | None = None
