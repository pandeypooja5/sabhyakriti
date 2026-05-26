"""SQLAlchemy 2.0 ORM models for the product schema."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CategoryModel(Base):
    __tablename__ = "categories"
    __table_args__ = (
        Index("ix_categories_type", "type"),
        Index("ix_categories_slug", "slug", unique=True),
        {"schema": "product"},
    )

    category_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    slug: Mapped[str] = mapped_column(sa.String(300), nullable=False, unique=True)
    type: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    display_order: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=sa.func.now(),
        nullable=False,
    )

    # Relationships
    product_categories: Mapped[list["ProductCategoryModel"]] = relationship(
        back_populates="category"
    )


class ProductModel(Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_sku", "sku", unique=True),
        Index("ix_products_slug", "slug", unique=True),
        Index("ix_products_is_active", "is_active"),
        Index("ix_products_created_at", "created_at"),
        Index("ix_products_search_vector", "search_vector", postgresql_using="gin"),
        {"schema": "product"},
    )

    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    sku: Mapped[str] = mapped_column(sa.String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    slug: Mapped[str] = mapped_column(sa.String(300), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    price: Mapped[Decimal] = mapped_column(
        sa.Numeric(12, 2), nullable=False
    )
    discount_percentage: Mapped[Decimal] = mapped_column(
        sa.Numeric(5, 2), nullable=False, default=Decimal("0.00")
    )
    stock_qty: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    average_rating: Mapped[Decimal] = mapped_column(
        sa.Numeric(3, 2), nullable=False, default=Decimal("0.00")
    )
    review_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    # Full-text search vector (maintained by DB trigger)
    search_vector: Mapped[Optional[str]] = mapped_column(
        TSVECTOR, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=sa.func.now(),
        nullable=False,
    )

    # Relationships
    images: Mapped[list["ProductImageModel"]] = relationship(
        back_populates="product",
        order_by="ProductImageModel.sort_order",
        cascade="all, delete-orphan",
    )
    product_categories: Mapped[list["ProductCategoryModel"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    reviews: Mapped[list["ReviewModel"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )


class ProductCategoryModel(Base):
    __tablename__ = "product_categories"
    __table_args__ = (
        Index("ix_product_categories_product_id", "product_id"),
        Index("ix_product_categories_category_id", "category_id"),
        {"schema": "product"},
    )

    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("product.products.product_id", ondelete="CASCADE"),
        primary_key=True,
    )
    category_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("product.categories.category_id", ondelete="CASCADE"),
        primary_key=True,
    )

    product: Mapped["ProductModel"] = relationship(back_populates="product_categories")
    category: Mapped["CategoryModel"] = relationship(back_populates="product_categories")


class ProductImageModel(Base):
    __tablename__ = "product_images"
    __table_args__ = (
        Index("ix_product_images_product_id", "product_id"),
        # Partial unique index: only one primary image per product
        Index(
            "uix_product_images_primary",
            "product_id",
            unique=True,
            postgresql_where=text("is_primary = true"),
        ),
        {"schema": "product"},
    )

    image_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("product.products.product_id", ondelete="CASCADE"),
        nullable=False,
    )
    s3_key: Mapped[str] = mapped_column(sa.String(500), nullable=False)
    cloudfront_url: Mapped[str] = mapped_column(sa.Text, nullable=False)
    is_primary: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    product: Mapped["ProductModel"] = relationship(back_populates="images")


class ReviewModel(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        Index("ix_reviews_product_id", "product_id"),
        Index("ix_reviews_user_id", "user_id"),
        # One review per user per product
        Index(
            "uix_reviews_user_product",
            "user_id",
            "product_id",
            unique=True,
        ),
        {"schema": "product"},
    )

    review_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("product.products.product_id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )
    rating: Mapped[int] = mapped_column(
        sa.SmallInteger,
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(sa.String(150), nullable=False)
    body: Mapped[str] = mapped_column(sa.Text, nullable=False)
    is_verified_purchase: Mapped[bool] = mapped_column(
        sa.Boolean, nullable=False, default=False
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=sa.func.now(),
        nullable=False,
    )

    product: Mapped["ProductModel"] = relationship(back_populates="reviews")
