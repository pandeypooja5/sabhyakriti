"""Data Transfer Objects for the Order service."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Shared / nested DTOs
# ---------------------------------------------------------------------------


class AddressSnapshotDTO(BaseModel):
    """Shipping address snapshot embedded in order responses."""

    model_config = ConfigDict(from_attributes=True)

    address_id: str
    full_name: str
    phone: str
    address_line1: str
    address_line2: str
    city: str
    state: str
    pincode: str


class OrderItemDTO(BaseModel):
    """Single order line item."""

    model_config = ConfigDict(from_attributes=True)

    order_item_id: UUID
    product_id: str
    variant_id: str | None = None
    product_name: str
    product_image_url: str
    unit_price: Decimal
    discounted_price: Decimal
    quantity: int
    hsn_code: str
    cgst_rate: Decimal
    sgst_rate: Decimal
    line_total: Decimal


class OrderDTO(BaseModel):
    """Full order detail response."""

    model_config = ConfigDict(from_attributes=True)

    order_id: UUID
    user_id: str
    order_number: str
    status: str
    payment_method: str
    payment_reference: str | None = None
    shipping_address: AddressSnapshotDTO
    subtotal: Decimal
    discount_amount: Decimal
    shipping_charge: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    total_amount: Decimal
    notes: str | None = None
    items: list[OrderItemDTO] = Field(default_factory=list)
    cancelled_at: datetime | None = None
    cancellation_reason: str | None = None
    confirmed_at: datetime | None = None
    shipped_at: datetime | None = None
    delivered_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class OrderSummaryDTO(BaseModel):
    """Lightweight order listing item (no items list)."""

    model_config = ConfigDict(from_attributes=True)

    order_id: UUID
    order_number: str
    status: str
    payment_method: str
    total_amount: Decimal
    item_count: int
    created_at: datetime


class PagedOrderListDTO(BaseModel):
    """Paginated list of orders."""

    items: list[OrderSummaryDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


# ---------------------------------------------------------------------------
# Address DTOs
# ---------------------------------------------------------------------------


class AddressDTO(BaseModel):
    """Full address response."""

    model_config = ConfigDict(from_attributes=True)

    address_id: UUID
    user_id: str
    full_name: str
    phone: str
    address_line1: str
    address_line2: str
    city: str
    state: str
    pincode: str
    is_default: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Return request DTOs
# ---------------------------------------------------------------------------


class ReturnItemDTO(BaseModel):
    """Single return line item."""

    model_config = ConfigDict(from_attributes=True)

    return_item_id: UUID
    order_item_id: UUID
    quantity: int
    reason: str


class ReturnRequestDTO(BaseModel):
    """Full return request response."""

    model_config = ConfigDict(from_attributes=True)

    return_request_id: UUID
    order_id: UUID
    user_id: str
    status: str
    reason: str
    items: list[ReturnItemDTO] = Field(default_factory=list)
    refund_amount: Decimal
    admin_notes: str | None = None
    processed_at: datetime | None = None
    items_received_at: datetime | None = None
    refund_initiated_at: datetime | None = None
    refunded_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Cart checkout DTO (received from Cart Service)
# ---------------------------------------------------------------------------


class CartItemDTO(BaseModel):
    """A single item from the cart service payload."""

    product_id: str
    variant_id: str | None = None
    product_name: str
    product_image_url: str
    unit_price: Decimal
    discounted_price: Decimal
    quantity: int
    hsn_code: str = "5208"


class CartCheckoutDTO(BaseModel):
    """Payload sent by Cart Service when initiating checkout."""

    cart_id: str
    items: list[CartItemDTO]
    subtotal: Decimal
    discount_amount: Decimal
    shipping_charge: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    total_amount: Decimal
    coupon_code: str | None = None


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class CreateOrderRequest(BaseModel):
    """Request body for creating an order (POST /api/v1/orders)."""

    address_id: UUID
    payment_method: str
    cart_data: CartCheckoutDTO
    notes: str | None = None

    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(cls, v: str) -> str:
        allowed = {"RAZORPAY", "UPI", "COD"}
        if v.upper() not in allowed:
            raise ValueError(f"payment_method must be one of {allowed}")
        return v.upper()


class CancelOrderRequest(BaseModel):
    """Request body for cancelling an order."""

    reason: str = Field(..., min_length=5, max_length=500)


class UpdateOrderStatusRequest(BaseModel):
    """Admin request to advance order status."""

    new_status: str
    notes: str | None = None

    @field_validator("new_status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"SHIPPED", "DELIVERED"}
        if v.upper() not in allowed:
            raise ValueError(f"new_status must be one of {allowed}")
        return v.upper()


class SubmitReturnItemRequest(BaseModel):
    """Single item in a return submission."""

    order_item_id: UUID
    quantity: int = Field(..., ge=1)
    reason: str = Field(..., min_length=5, max_length=500)


class SubmitReturnRequest(BaseModel):
    """Request body for submitting a return request."""

    reason: str = Field(..., min_length=5, max_length=500)
    items: list[SubmitReturnItemRequest] = Field(..., min_length=1)


class ProcessReturnRequest(BaseModel):
    """Admin request to approve or reject a return."""

    action: str  # "APPROVE" | "REJECT"
    admin_notes: str | None = None

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        allowed = {"APPROVE", "REJECT"}
        if v.upper() not in allowed:
            raise ValueError(f"action must be one of {allowed}")
        return v.upper()


# ---------------------------------------------------------------------------
# Address request bodies
# ---------------------------------------------------------------------------


class CreateAddressRequest(BaseModel):
    """Request body for adding a new address."""

    full_name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., pattern=r"^\+?[0-9]{10,15}$")
    address_line1: str = Field(..., min_length=5, max_length=200)
    address_line2: str = Field(default="", max_length=200)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    pincode: str = Field(..., pattern=r"^[0-9]{6}$")


class UpdateAddressRequest(BaseModel):
    """Request body for updating an existing address (all fields optional)."""

    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    phone: str | None = Field(default=None, pattern=r"^\+?[0-9]{10,15}$")
    address_line1: str | None = Field(default=None, min_length=5, max_length=200)
    address_line2: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    state: str | None = Field(default=None, min_length=2, max_length=100)
    pincode: str | None = Field(default=None, pattern=r"^[0-9]{6}$")


# ---------------------------------------------------------------------------
# Internal endpoint DTOs
# ---------------------------------------------------------------------------


class ConfirmOrderRequest(BaseModel):
    """Payload from Payment Service to confirm an order."""

    payment_reference: str
    payment_method: str


class VerifiedPurchaseResponse(BaseModel):
    """Response for Product Service review-eligibility check."""

    user_id: str
    product_id: str
    order_id: UUID
    order_number: str
    is_eligible: bool
    delivered_at: datetime | None = None


# ---------------------------------------------------------------------------
# Generic paginated list helper
# ---------------------------------------------------------------------------


class PaginationParams(BaseModel):
    """Common query parameters for paginated endpoints."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
