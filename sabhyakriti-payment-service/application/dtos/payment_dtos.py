"""Pydantic v2 DTOs (Data Transfer Objects) for the payment service.

These schemas define the shape of data flowing across layer boundaries —
from HTTP request bodies, through the application service, to HTTP responses.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from domain.value_objects import PaymentMethod, PaymentStatus


# ---------------------------------------------------------------------------
# Inbound (request) schemas
# ---------------------------------------------------------------------------


class CreateOrderRequest(BaseModel):
    """Request to create a Razorpay order for a given platform order."""

    model_config = ConfigDict(frozen=True)

    order_id: UUID
    amount: Decimal = Field(gt=0, description="Amount in INR (rupees, not paise)")
    currency: str = Field(default="INR", max_length=3)


class VerifyPaymentRequest(BaseModel):
    """Payload sent by the frontend after completing Razorpay checkout."""

    model_config = ConfigDict(frozen=True)

    order_id: UUID
    razorpay_payment_id: str = Field(min_length=1)
    razorpay_order_id: str = Field(min_length=1)
    razorpay_signature: str = Field(min_length=1)


class CODConfirmRequest(BaseModel):
    """Internal request to confirm a Cash-on-Delivery payment."""

    model_config = ConfigDict(frozen=True)

    order_id: UUID
    amount: Decimal = Field(gt=0, description="Amount in INR")
    user_id: UUID


class RefundRequest(BaseModel):
    """Internal request from Order Service to refund a captured payment."""

    model_config = ConfigDict(frozen=True)

    order_id: UUID
    amount: Decimal = Field(gt=0, description="Refund amount in INR")


# ---------------------------------------------------------------------------
# Outbound (response) schemas
# ---------------------------------------------------------------------------


class RazorpayOrderDTO(BaseModel):
    """Response returned to the frontend to initialise the Razorpay checkout modal."""

    model_config = ConfigDict(frozen=True)

    razorpay_order_id: str
    razorpay_key_id: str
    amount: int = Field(description="Amount in paise")
    currency: str
    order_id: UUID


class PaymentDTO(BaseModel):
    """Representation of a payment returned to callers."""

    model_config = ConfigDict(frozen=True)

    payment_id: UUID
    order_id: UUID
    status: PaymentStatus
    method: PaymentMethod
    amount: Decimal
    razorpay_payment_id: str | None = None
    captured_at: datetime | None = None
    refund_id: str | None = None
    refund_amount: Decimal | None = None
    refunded_at: datetime | None = None


class PaymentReceiptDTO(BaseModel):
    """Receipt shown to the user after a successful payment."""

    model_config = ConfigDict(frozen=True)

    order_id: UUID
    order_number: str
    payment_id: UUID
    razorpay_payment_id: str | None = None
    method: PaymentMethod
    amount: Decimal
    captured_at: datetime
    status: PaymentStatus


class RefundDTO(BaseModel):
    """Response returned after initiating a refund."""

    model_config = ConfigDict(frozen=True)

    refund_id: str
    order_id: UUID
    amount: Decimal
    status: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Webhook schemas
# ---------------------------------------------------------------------------


class WebhookPaymentEntity(BaseModel):
    """Minimal representation of the ``payment.entity`` inside a Razorpay webhook."""

    model_config = ConfigDict(extra="allow")

    id: str
    order_id: str | None = None
    status: str | None = None
    amount: int | None = None
    currency: str | None = None


class WebhookPayload(BaseModel):
    """Razorpay webhook payload wrapper."""

    model_config = ConfigDict(extra="allow")

    payment: dict | None = None  # type: ignore[type-arg]


class WebhookEventPayload(BaseModel):
    """Top-level Razorpay webhook body."""

    model_config = ConfigDict(extra="allow")

    event: str
    payload: WebhookPayload | None = None
    created_at: int | None = None  # Unix timestamp from Razorpay
