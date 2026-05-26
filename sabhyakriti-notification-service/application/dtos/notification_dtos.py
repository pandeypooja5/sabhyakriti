"""Pydantic v2 request DTOs for all notification types."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, field_validator


class OrderItemDTO(BaseModel):
    """A single line item within an order."""

    name: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)
    unit_price: Decimal = Field(..., ge=Decimal("0"))
    total_price: Decimal = Field(..., ge=Decimal("0"))


# ── Email Requests ─────────────────────────────────────────────────────────────


class EmailVerificationRequest(BaseModel):
    """Request to send an account email-verification message."""

    to_email: EmailStr
    full_name: str = Field(..., min_length=1)
    verification_link: str = Field(..., min_length=1)


class PasswordResetRequest(BaseModel):
    """Request to send a password-reset email."""

    to_email: EmailStr
    full_name: str = Field(..., min_length=1)
    reset_link: str = Field(..., min_length=1)


class OrderConfirmationRequest(BaseModel):
    """Request to send an order-confirmation email."""

    to_email: EmailStr
    full_name: str = Field(..., min_length=1)
    order_number: str = Field(..., min_length=1)
    items: list[OrderItemDTO] = Field(..., min_length=1)
    subtotal: Decimal = Field(..., ge=Decimal("0"))
    discount_amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    gst_amount: Decimal = Field(..., ge=Decimal("0"))
    total: Decimal = Field(..., ge=Decimal("0"))
    shipping_address: dict[str, str]
    payment_method: str = Field(..., min_length=1)


class OrderShippedRequest(BaseModel):
    """Request to send an order-shipped notification (email + optional SMS)."""

    to_email: EmailStr
    to_phone: str | None = None
    full_name: str = Field(..., min_length=1)
    order_number: str = Field(..., min_length=1)
    tracking_number: str = Field(..., min_length=1)
    courier_name: str = Field(..., min_length=1)


class OrderDeliveredRequest(BaseModel):
    """Request to send an order-delivered notification (email + optional SMS)."""

    to_email: EmailStr
    to_phone: str | None = None
    full_name: str = Field(..., min_length=1)
    order_number: str = Field(..., min_length=1)
    delivered_at: datetime


class OrderCancelledRequest(BaseModel):
    """Request to send an order-cancellation email."""

    to_email: EmailStr
    full_name: str = Field(..., min_length=1)
    order_number: str = Field(..., min_length=1)
    reason: str | None = None


class ReturnReceivedRequest(BaseModel):
    """Request to send a return-received confirmation email."""

    to_email: EmailStr
    full_name: str = Field(..., min_length=1)
    order_number: str = Field(..., min_length=1)
    return_id: str = Field(..., min_length=1)
    items: list[str] = Field(..., min_length=1)


class ReturnApprovedRequest(BaseModel):
    """Request to send a return-approved email with refund amount."""

    to_email: EmailStr
    full_name: str = Field(..., min_length=1)
    order_number: str = Field(..., min_length=1)
    refund_amount: Decimal = Field(..., ge=Decimal("0"))


class RefundProcessedRequest(BaseModel):
    """Request to send a refund-processed confirmation email."""

    to_email: EmailStr
    full_name: str = Field(..., min_length=1)
    order_number: str = Field(..., min_length=1)
    refund_amount: Decimal = Field(..., ge=Decimal("0"))


class PaymentReceiptRequest(BaseModel):
    """Request to send a payment-receipt email."""

    to_email: EmailStr
    full_name: str = Field(..., min_length=1)
    order_number: str = Field(..., min_length=1)
    payment_id: str = Field(..., min_length=1)
    method: str = Field(..., min_length=1)
    amount: Decimal = Field(..., ge=Decimal("0"))
    gst_amount: Decimal = Field(..., ge=Decimal("0"))
    captured_at: datetime


# ── SMS Requests ───────────────────────────────────────────────────────────────


class OTPSMSRequest(BaseModel):
    """Request to send an OTP via SMS."""

    to_phone: str = Field(..., min_length=10)
    otp_code: str = Field(..., min_length=4, max_length=8)

    @field_validator("otp_code")
    @classmethod
    def otp_must_be_digits(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("otp_code must contain only digits")
        return v


class OrderShippedSMSRequest(BaseModel):
    """Request to send an order-shipped SMS."""

    to_phone: str = Field(..., min_length=10)
    order_number: str = Field(..., min_length=1)
    courier_name: str = Field(..., min_length=1)
    tracking_number: str = Field(..., min_length=1)


class OrderDeliveredSMSRequest(BaseModel):
    """Request to send an order-delivered SMS."""

    to_phone: str = Field(..., min_length=10)
    order_number: str = Field(..., min_length=1)
