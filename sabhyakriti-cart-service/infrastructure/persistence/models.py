"""SQLAlchemy ORM models for the cart service.

All tables live in the `cart` PostgreSQL schema.
Uses SQLAlchemy 2.0 Mapped[] syntax throughout.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.persistence.database import Base

_SCHEMA = "cart"


class CartModel(Base):
    """Persisted cart — one per user, never deleted."""

    __tablename__ = "carts"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_carts_user_id"),
        {"schema": _SCHEMA},
    )

    cart_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    applied_coupon_code: Mapped[str | None] = mapped_column(
        String(50), nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    items: Mapped[list[CartItemModel]] = relationship(
        "CartItemModel",
        back_populates="cart",
        cascade="all, delete-orphan",
        lazy="select",
    )


class CartItemModel(Base):
    """A product line in a cart.

    UNIQUE(cart_id, product_id) enforced at DB level.
    quantity CHECK ensures 1 <= quantity <= 10.
    """

    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("cart_id", "product_id", name="uq_cart_items_cart_product"),
        CheckConstraint("quantity >= 1 AND quantity <= 10", name="ck_cart_items_quantity"),
        {"schema": _SCHEMA},
    )

    cart_item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    cart_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(f"{_SCHEMA}.carts.cart_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    cart: Mapped[CartModel] = relationship("CartModel", back_populates="items")


class WishlistModel(Base):
    """Persisted wishlist — one per user."""

    __tablename__ = "wishlists"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_wishlists_user_id"),
        {"schema": _SCHEMA},
    )

    wishlist_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    items: Mapped[list[WishlistItemModel]] = relationship(
        "WishlistItemModel",
        back_populates="wishlist",
        cascade="all, delete-orphan",
        lazy="select",
    )


class WishlistItemModel(Base):
    """A product in a wishlist.

    UNIQUE(wishlist_id, product_id) — add same product = idempotent.
    """

    __tablename__ = "wishlist_items"
    __table_args__ = (
        UniqueConstraint(
            "wishlist_id", "product_id", name="uq_wishlist_items_wishlist_product"
        ),
        {"schema": _SCHEMA},
    )

    wishlist_item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    wishlist_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(f"{_SCHEMA}.wishlists.wishlist_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    wishlist: Mapped[WishlistModel] = relationship(
        "WishlistModel", back_populates="items"
    )


class CouponModel(Base):
    """Discount coupon.

    used_count is incremented by Order Service, not Cart Service.
    """

    __tablename__ = "coupons"
    __table_args__ = (
        UniqueConstraint("code", name="uq_coupons_code"),
        CheckConstraint("value > 0", name="ck_coupons_value_positive"),
        CheckConstraint(
            "min_order_amount >= 0", name="ck_coupons_min_order_non_negative"
        ),
        CheckConstraint("used_count >= 0", name="ck_coupons_used_count_non_negative"),
        {"schema": _SCHEMA},
    )

    coupon_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    coupon_type: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # "FLAT" | "PERCENT"
    value: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2), nullable=False
    )
    min_order_amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2), nullable=False, default=Decimal("0")
    )
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
