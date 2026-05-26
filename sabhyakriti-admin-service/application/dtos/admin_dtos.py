"""Admin service Data Transfer Objects (Pydantic v2 schemas)."""

from __future__ import annotations

import math
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OrderSummaryDTO(BaseModel):
    """Summary of a single order for admin views."""

    model_config = ConfigDict(populate_by_name=True)

    order_id: UUID
    order_number: str
    user_id: UUID
    status: str
    total_amount: Decimal = Field(decimal_places=2)
    placed_at: datetime
    item_count: int


class RevenueDayDTO(BaseModel):
    """Revenue aggregated per calendar day."""

    model_config = ConfigDict(populate_by_name=True)

    date: str  # ISO date string YYYY-MM-DD for JSON serialisation simplicity
    revenue: Decimal = Field(decimal_places=2)
    order_count: int


class TopProductDTO(BaseModel):
    """Top-selling product over a date range."""

    model_config = ConfigDict(populate_by_name=True)

    product_id: UUID
    product_name: str
    units_sold: int
    revenue: Decimal = Field(decimal_places=2)


class CategoryRevenueDTO(BaseModel):
    """Revenue by product category."""

    model_config = ConfigDict(populate_by_name=True)

    category_name: str
    category_type: str
    revenue: Decimal = Field(decimal_places=2)


class DashboardDTO(BaseModel):
    """Admin dashboard KPIs covering the last 30 rolling days."""

    model_config = ConfigDict(populate_by_name=True)

    revenue_30d: Decimal = Field(decimal_places=2)
    orders_30d: int
    new_customers_30d: int
    low_stock_products: int
    pending_orders: int
    pending_returns: int
    recent_orders: list[OrderSummaryDTO] = Field(default_factory=list)
    service_unavailable: bool = False


class SalesReportDTO(BaseModel):
    """Sales report for a configurable date range (max 365 days)."""

    model_config = ConfigDict(populate_by_name=True)

    from_date: str  # YYYY-MM-DD
    to_date: str  # YYYY-MM-DD
    total_revenue: Decimal = Field(decimal_places=2)
    total_orders: int
    revenue_by_day: list[RevenueDayDTO] = Field(default_factory=list)
    top_products: list[TopProductDTO] = Field(default_factory=list)
    category_revenue: list[CategoryRevenueDTO] = Field(default_factory=list)
    order_status_breakdown: dict[str, int] = Field(default_factory=dict)
    service_unavailable: bool = False


class CustomerSummaryDTO(BaseModel):
    """Lightweight customer record for list views."""

    model_config = ConfigDict(populate_by_name=True)

    user_id: UUID
    email: str | None = None
    phone_number: str | None = None
    full_name: str
    is_email_verified: bool
    created_at: datetime
    total_orders: int


class CustomerDetailDTO(BaseModel):
    """Full customer profile including order history."""

    model_config = ConfigDict(populate_by_name=True)

    user: CustomerSummaryDTO
    orders: list[OrderSummaryDTO] = Field(default_factory=list)


class PagedCustomerListDTO(BaseModel):
    """Paginated customer list response."""

    model_config = ConfigDict(populate_by_name=True)

    items: list[CustomerSummaryDTO]
    total_count: int
    page: int
    page_size: int
    total_pages: int

    @model_validator(mode="before")
    @classmethod
    def compute_total_pages(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Auto-compute total_pages if not explicitly supplied."""
        total_count = values.get("total_count", 0)
        page_size = values.get("page_size", 1)
        if page_size and "total_pages" not in values:
            values["total_pages"] = max(1, math.ceil(total_count / page_size))
        return values
