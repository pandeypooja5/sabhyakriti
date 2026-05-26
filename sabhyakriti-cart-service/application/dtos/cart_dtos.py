"""Pydantic v2 DTOs (request/response schemas) for the cart service."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Shared config
# ---------------------------------------------------------------------------

class _BaseDTO(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


# ---------------------------------------------------------------------------
# Cart DTOs
# ---------------------------------------------------------------------------

class CartItemDTO(_BaseDTO):
    """A single item as returned in the cart response."""

    cart_item_id: UUID
    product_id: UUID
    product_name: str
    primary_image_url: str | None = None
    discounted_price: Decimal
    quantity: int
    item_total: Decimal
    stock_status: str
    is_available: bool
    price_stale: bool = False


class CartTotalsDTO(_BaseDTO):
    """Pricing totals for the cart.

    Monetary fields serialised as strings to preserve decimal precision
    in JSON transport (avoids IEEE 754 float representation issues).
    """

    subtotal: Decimal
    discount_amount: Decimal
    gst_amount: Decimal
    shipping_charge: Decimal
    total: Decimal
    coupon_code: str | None = None
    price_stale: bool = False

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: str},
    )


class CartDTO(_BaseDTO):
    """Full cart response including items and totals."""

    cart_id: UUID
    items: list[CartItemDTO]
    totals: CartTotalsDTO
    item_count: int


# ---------------------------------------------------------------------------
# Wishlist DTOs
# ---------------------------------------------------------------------------

class WishlistItemDTO(_BaseDTO):
    """A single item as returned in the wishlist response."""

    wishlist_item_id: UUID
    product_id: UUID
    product_name: str
    primary_image_url: str | None = None
    discounted_price: Decimal
    stock_status: str
    is_available: bool


class WishlistDTO(_BaseDTO):
    """Full wishlist response."""

    wishlist_id: UUID
    items: list[WishlistItemDTO]


# ---------------------------------------------------------------------------
# Coupon DTOs
# ---------------------------------------------------------------------------

class CouponDTO(_BaseDTO):
    """Coupon representation (admin + applied coupon summary)."""

    coupon_id: UUID
    code: str
    coupon_type: str = Field(alias="type", default="")
    value: Decimal
    min_order_amount: Decimal
    max_uses: int | None = None
    used_count: int
    is_active: bool
    expires_at: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


# ---------------------------------------------------------------------------
# Internal (Order Service) DTOs
# ---------------------------------------------------------------------------

class CheckoutItemDTO(_BaseDTO):
    """A single item in the checkout payload sent to Order Service."""

    product_id: UUID
    quantity: int
    unit_price: Decimal
    item_total: Decimal


class CartCheckoutDTO(_BaseDTO):
    """Full cart payload for internal Order Service consumption.

    Used by GET /internal/v1/cart/{user_id}.
    """

    cart_id: UUID
    user_id: UUID
    items: list[CheckoutItemDTO]
    totals: CartTotalsDTO
    coupon_code: str | None = None


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class AddToCartRequest(BaseModel):
    """Request body for POST /api/v1/cart/items."""

    product_id: UUID
    quantity: int = Field(ge=1, le=10)


class UpdateQuantityRequest(BaseModel):
    """Request body for PATCH /api/v1/cart/items/{cart_item_id}.

    quantity=0 signals item removal.
    """

    quantity: int = Field(ge=0, le=10)


class ApplyCouponRequest(BaseModel):
    """Request body for POST /api/v1/cart/coupon."""

    coupon_code: str = Field(min_length=1, max_length=50)

    @field_validator("coupon_code")
    @classmethod
    def normalise_code(cls, v: str) -> str:
        """Normalise coupon code to uppercase and strip whitespace."""
        return v.strip().upper()


class AddToWishlistRequest(BaseModel):
    """Request body for POST /api/v1/wishlist/items."""

    product_id: UUID


class CreateCouponRequest(BaseModel):
    """Request body for POST /api/v1/admin/coupons."""

    code: str = Field(min_length=1, max_length=50)
    coupon_type: str = Field(alias="type")
    value: Decimal = Field(gt=Decimal("0"))
    min_order_amount: Decimal = Field(ge=Decimal("0"), default=Decimal("0"))
    max_uses: int | None = Field(default=None, ge=1)
    expires_at: datetime | None = None

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("code")
    @classmethod
    def normalise_code(cls, v: str) -> str:
        return v.strip().upper()


class UpdateCouponRequest(BaseModel):
    """Request body for PATCH /api/v1/admin/coupons/{coupon_id}.

    All fields optional — only provided fields are updated.
    """

    value: Decimal | None = Field(default=None, gt=Decimal("0"))
    min_order_amount: Decimal | None = Field(default=None, ge=Decimal("0"))
    max_uses: int | None = Field(default=None, ge=1)
    expires_at: datetime | None = None
    is_active: bool | None = None
