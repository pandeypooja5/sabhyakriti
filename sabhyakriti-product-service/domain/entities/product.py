"""Product domain entities."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from domain.value_objects import StockStatus

_LOW_STOCK_THRESHOLD = 5


@dataclass
class ProductImage:
    """Domain entity for a product image."""

    image_id: UUID
    product_id: UUID
    s3_key: str
    cloudfront_url: str
    is_primary: bool
    sort_order: int
    created_at: datetime


@dataclass
class Product:
    """Core product domain entity."""

    product_id: UUID
    sku: str
    name: str
    slug: str
    description: str
    price: Decimal
    discount_percentage: Decimal
    stock_qty: int
    is_active: bool
    average_rating: Decimal
    review_count: int
    created_at: datetime
    updated_at: datetime
    fabric: str | None = None
    color: str | None = None
    work: str | None = None
    saree_length: Decimal | None = None
    blouse_length: Decimal | None = None
    blouse_included: bool = False
    images: list[ProductImage] = field(default_factory=list)
    category_ids: list[UUID] = field(default_factory=list)

    @property
    def discounted_price(self) -> Decimal:
        """Calculate final price after discount."""
        return (self.price * (1 - self.discount_percentage / 100)).quantize(
            Decimal("0.01")
        )

    @property
    def stock_status(self) -> StockStatus:
        """Derive stock status from quantity."""
        if self.stock_qty <= 0:
            return StockStatus.OUT_OF_STOCK
        if self.stock_qty <= _LOW_STOCK_THRESHOLD:
            return StockStatus.LOW_STOCK
        return StockStatus.IN_STOCK

    @property
    def savings_amount(self) -> Decimal:
        """Amount saved due to discount."""
        return (self.price - self.discounted_price).quantize(Decimal("0.01"))

    @property
    def primary_image(self) -> ProductImage | None:
        """Return the primary image if available."""
        for img in self.images:
            if img.is_primary:
                return img
        return self.images[0] if self.images else None
