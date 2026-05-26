"""
SQLAlchemy ORM models for the `order` PostgreSQL schema.

The schema name `order` is a reserved word in SQL and must be quoted
everywhere it appears — handled via `schema='"order"'` on MetaData and
`__table_args__`.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Schema name constant — must be quoted because it's a SQL reserved word
_SCHEMA = "order"


class Base(DeclarativeBase):
    pass


class OrderModel(Base):
    """Persisted order aggregate root."""

    __tablename__ = "orders"
    __table_args__ = {"schema": _SCHEMA}

    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    order_number: Mapped[str] = mapped_column(
        String(30), nullable=False, unique=True, index=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # JSONB snapshot of shipping address at order creation
    shipping_address: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    shipping_charge: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    cgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    sgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status timestamps
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    shipped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    items: Mapped[list[OrderItemModel]] = relationship(
        "OrderItemModel",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class OrderItemModel(Base):
    """Persisted order line item with product snapshot."""

    __tablename__ = "order_items"
    __table_args__ = {"schema": _SCHEMA}

    order_item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True
    )
    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(f"{_SCHEMA}.orders.order_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    variant_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Snapshot columns — captured at order creation
    product_name: Mapped[str] = mapped_column(String(300), nullable=False)
    product_image_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discounted_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    hsn_code: Mapped[str] = mapped_column(
        String(10), nullable=False, default="5208"
    )
    cgst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("2.5")
    )
    sgst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("2.5")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationship
    order: Mapped[OrderModel] = relationship(
        "OrderModel", back_populates="items"
    )


class AddressModel(Base):
    """Persisted user shipping address."""

    __tablename__ = "addresses"
    __table_args__ = {"schema": _SCHEMA}

    address_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    address_line1: Mapped[str] = mapped_column(String(200), nullable=False)
    address_line2: Mapped[str] = mapped_column(
        String(200), nullable=False, default=""
    )
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False)
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class ReturnRequestModel(Base):
    """Persisted return request."""

    __tablename__ = "return_requests"
    __table_args__ = {"schema": _SCHEMA}

    return_request_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True
    )
    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(f"{_SCHEMA}.orders.order_id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,  # one return request per order
        index=True,
    )
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    refund_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Timestamps
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    items_received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    refund_initiated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    refunded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    items: Mapped[list[ReturnItemModel]] = relationship(
        "ReturnItemModel",
        back_populates="return_request",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ReturnItemModel(Base):
    """A single item in a return request."""

    __tablename__ = "return_items"
    __table_args__ = {"schema": _SCHEMA}

    return_item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True
    )
    return_request_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            f"{_SCHEMA}.return_requests.return_request_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    order_item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            f"{_SCHEMA}.order_items.order_item_id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationship
    return_request: Mapped[ReturnRequestModel] = relationship(
        "ReturnRequestModel", back_populates="items"
    )
