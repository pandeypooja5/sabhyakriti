"""Pydantic v2 DTOs for the product service."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from domain.value_objects import CategoryType, SortOrder, StockStatus

# ---------------------------------------------------------------------------
# Shared / output DTOs
# ---------------------------------------------------------------------------


class CategoryDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category_id: UUID
    name: str
    type: CategoryType
    slug: str
    display_order: int


class ProductImageDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    image_id: UUID
    cloudfront_url: str
    is_primary: bool
    sort_order: int


class ReviewDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    review_id: UUID
    product_id: UUID
    user_id: UUID
    rating: int
    title: str
    body: str
    is_verified_purchase: bool
    created_at: datetime


class PagedReviewsDTO(BaseModel):
    items: list[ReviewDTO]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class ProductSummaryDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: UUID
    name: str
    slug: str
    sku: str = ""
    discounted_price: Decimal
    price: Decimal
    discount_percentage: Decimal
    savings_amount: Decimal
    stock_status: StockStatus
    stock_qty: int = 0
    primary_image_url: str | None
    average_rating: Decimal
    review_count: int


class ProductDetailDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: UUID
    sku: str
    name: str
    slug: str
    description: str
    price: Decimal
    discount_percentage: Decimal
    discounted_price: Decimal
    savings_amount: Decimal
    stock_qty: int
    stock_status: StockStatus
    fabric: str | None = None
    color: str | None = None
    work: str | None = None
    saree_length: Decimal | None = None
    blouse_length: Decimal | None = None
    blouse_included: bool = False
    average_rating: Decimal
    review_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    images: list[ProductImageDTO]
    # keyed by CategoryType string: {"FABRIC": [...], "OCCASION": [...], ...}
    categories: dict[str, list[CategoryDTO]]
    reviews: PagedReviewsDTO
    related_products: list[ProductSummaryDTO]


class PagedProductListDTO(BaseModel):
    items: list[ProductSummaryDTO]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class PresignedUrlDTO(BaseModel):
    presigned_url: str
    s3_key: str
    expires_in: int


class BulkImportResultDTO(BaseModel):
    imported_count: int
    updated_count: int
    failed_rows: list[dict]  # type: ignore[type-arg]


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

_NAME_MAX = 255
_SKU_MAX = 100
_DESCRIPTION_MAX = 10_000
_TITLE_MAX = 150
_BODY_MAX = 2_000


class CreateProductRequest(BaseModel):
    sku: Annotated[str, Field(min_length=1, max_length=_SKU_MAX)]
    name: Annotated[str, Field(min_length=1, max_length=_NAME_MAX)]
    description: Annotated[str, Field(min_length=0, max_length=_DESCRIPTION_MAX)] = ""
    price: Annotated[Decimal, Field(gt=Decimal("0"))]
    discount_percentage: Annotated[
        Decimal, Field(ge=Decimal("0"), le=Decimal("100"))
    ] = Decimal("0")
    stock_qty: Annotated[int, Field(ge=0)] = 0
    fabric: str | None = None
    color: str | None = None
    work: str | None = None
    saree_length: Decimal | None = None
    blouse_length: Decimal | None = None
    blouse_included: bool = False
    category_ids: list[UUID] = Field(default_factory=list)


class UpdateProductRequest(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=_NAME_MAX)] | None = None
    description: Annotated[str, Field(max_length=_DESCRIPTION_MAX)] | None = None
    price: Annotated[Decimal, Field(gt=Decimal("0"))] | None = None
    discount_percentage: Annotated[
        Decimal, Field(ge=Decimal("0"), le=Decimal("100"))
    ] | None = None
    stock_qty: Annotated[int, Field(ge=0)] | None = None
    fabric: str | None = None
    color: str | None = None
    work: str | None = None
    saree_length: Decimal | None = None
    blouse_length: Decimal | None = None
    blouse_included: bool | None = None
    category_ids: list[UUID] | None = None
    is_active: bool | None = None


class SubmitReviewRequest(BaseModel):
    product_id: UUID
    rating: Annotated[int, Field(ge=1, le=5)]
    title: Annotated[str, Field(min_length=1, max_length=_TITLE_MAX)]
    body: Annotated[str, Field(min_length=1, max_length=_BODY_MAX)]


class CreateCategoryRequest(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=_NAME_MAX)]
    type: CategoryType
    display_order: int = 0


class UpdateCategoryRequest(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=_NAME_MAX)] | None = None
    display_order: int | None = None
    is_active: bool | None = None


class ConfirmImageUploadRequest(BaseModel):
    s3_key: str
    is_primary: bool = False
    sort_order: int = 0

    @field_validator("s3_key")
    @classmethod
    def s3_key_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("s3_key must not be empty")
        return v


class StockDeltaRequest(BaseModel):
    delta: int = Field(..., description="Positive = reserve, negative = release")

    @field_validator("delta")
    @classmethod
    def delta_not_zero(cls, v: int) -> int:
        if v == 0:
            raise ValueError("delta must be non-zero")
        return v
