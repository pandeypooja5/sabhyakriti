"""SQLAlchemy ORM models for the ``payment`` PostgreSQL schema.

Both tables live in the ``payment`` schema to keep concerns separated
from other microservice schemas in the shared database.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.persistence.database import Base

SCHEMA = "payment"


class PaymentModel(Base):
    """Persistent representation of a payment aggregate."""

    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("order_id", name="uq_payments_order_id"),
        {"schema": SCHEMA},
    )

    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")

    method: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    razorpay_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, unique=True, index=True
    )
    razorpay_signature: Mapped[str | None] = mapped_column(String(255), nullable=True)

    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    first_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    refund_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    refund_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # webhook_events relationship removed — use WebhookEventModel.payment (viewonly) instead


class WebhookEventModel(Base):
    """Idempotent store for incoming Razorpay webhook events.

    The UNIQUE constraint on ``razorpay_event_id`` ensures each event is
    processed exactly once via INSERT ... ON CONFLICT DO NOTHING.
    """

    __tablename__ = "webhook_events"
    __table_args__ = (
        UniqueConstraint("razorpay_event_id", name="uq_webhook_events_razorpay_event_id"),
        {"schema": SCHEMA},
    )

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    razorpay_event_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)  # type: ignore[type-arg]

    processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Denormalised reference for easy join (nullable — some events may not
    # have a payment_id yet at receipt time)
    razorpay_payment_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Soft relationship back to payment (viewonly — no FK, events can arrive before payments)
    payment: Mapped[PaymentModel | None] = relationship(
        "PaymentModel",
        foreign_keys=[razorpay_payment_id],
        primaryjoin=(
            "WebhookEventModel.razorpay_payment_id == foreign(PaymentModel.razorpay_payment_id)"
        ),
        lazy="noload",
        viewonly=True,
    )
