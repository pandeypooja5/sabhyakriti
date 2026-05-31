"""Admin Application Service — orchestrates downstream fan-out calls."""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

import structlog

from application.clients.auth_service_client import AuthServiceClient
from application.clients.order_service_client import OrderServiceClient
from application.clients.product_service_client import ProductServiceClient
from application.dtos.admin_dtos import (
    CategoryRevenueDTO,
    CustomerDetailDTO,
    CustomerSummaryDTO,
    DashboardDTO,
    OrderSummaryDTO,
    PagedCustomerListDTO,
    RevenueDayDTO,
    SalesReportDTO,
    TopProductDTO,
)

logger = structlog.get_logger(__name__)

_MAX_REPORT_DAYS = 365


def _parse_order(raw: dict[str, Any]) -> OrderSummaryDTO:
    """Map a raw order dict from the Order Service to an OrderSummaryDTO."""
    placed_at_raw = raw.get("placed_at") or raw.get("created_at", "2000-01-01T00:00:00Z")
    return OrderSummaryDTO(
        order_id=UUID(str(raw["order_id"])),
        order_number=str(raw["order_number"]),
        user_id=UUID(str(raw["user_id"])) if raw.get("user_id") else UUID(int=0),
        status=str(raw["status"]),
        total_amount=Decimal(str(raw.get("total_amount", "0"))),
        placed_at=datetime.fromisoformat(str(placed_at_raw).replace("Z", "+00:00")),
        item_count=int(raw.get("item_count", 0)),
    )


def _parse_customer(raw: dict[str, Any], total_orders: int = 0) -> CustomerSummaryDTO:
    """Map a raw customer dict from the Auth Service to a CustomerSummaryDTO."""
    return CustomerSummaryDTO(
        user_id=UUID(str(raw["user_id"])),
        email=raw.get("email"),
        phone_number=raw.get("phone_number"),
        full_name=str(raw.get("full_name", "")),
        is_email_verified=bool(raw.get("is_email_verified", False)),
        created_at=datetime.fromisoformat(str(raw["created_at"])),
        total_orders=int(raw.get("total_orders", total_orders)),
    )


class AdminApplicationService:
    """Aggregates data from downstream services for admin workflows."""

    def __init__(
        self,
        order_client: OrderServiceClient,
        product_client: ProductServiceClient,
        auth_client: AuthServiceClient,
    ) -> None:
        self._order = order_client
        self._product = product_client
        self._auth = auth_client

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    async def get_dashboard(self) -> DashboardDTO:
        """Build dashboard KPIs using parallel fan-out to all downstream services.

        If any individual service call fails the dashboard is still returned
        with safe defaults and ``service_unavailable=True``.
        """
        now = datetime.now(tz=timezone.utc)
        days = 30

        stats_task = self._order.get_dashboard_stats(days=days)
        pending_task = self._order.get_pending_counts()
        recent_task = self._order.get_recent_orders(limit=10)
        low_stock_task = self._product.get_low_stock_count()
        new_customers_task = self._auth.get_new_customers_count(
            since=datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
            .__class__(now.year, now.month, now.day, tzinfo=timezone.utc)
        )

        results = await asyncio.gather(
            stats_task,
            pending_task,
            recent_task,
            low_stock_task,
            new_customers_task,
            return_exceptions=True,
        )

        stats_result, pending_result, recent_result, low_stock_result, new_cust_result = results

        service_unavailable = False

        # --- order stats ---
        if isinstance(stats_result, BaseException):
            logger.error("dashboard.order_stats unavailable", exc_info=stats_result)
            revenue_30d = Decimal("0")
            orders_30d = 0
            service_unavailable = True
        else:
            stats_dict: dict[str, Any] = stats_result  # type: ignore[assignment]
            revenue_30d = Decimal(str(stats_dict.get("revenue", "0")))
            orders_30d = int(stats_dict.get("order_count", 0))

        # --- pending counts ---
        if isinstance(pending_result, BaseException):
            logger.error("dashboard.pending_counts unavailable", exc_info=pending_result)
            pending_orders = 0
            pending_returns = 0
            service_unavailable = True
        else:
            pending_dict: dict[str, Any] = pending_result  # type: ignore[assignment]
            pending_orders = int(pending_dict.get("pending_orders", 0))
            pending_returns = int(pending_dict.get("pending_returns", 0))

        # --- recent orders ---
        if isinstance(recent_result, BaseException):
            logger.error("dashboard.recent_orders unavailable", exc_info=recent_result)
            recent_orders: list[OrderSummaryDTO] = []
            service_unavailable = True
        else:
            raw_orders: list[dict[str, Any]] = recent_result  # type: ignore[assignment]
            recent_orders = [_parse_order(o) for o in raw_orders]

        # --- low stock ---
        if isinstance(low_stock_result, BaseException):
            logger.error("dashboard.low_stock unavailable", exc_info=low_stock_result)
            low_stock_products = 0
            service_unavailable = True
        else:
            low_stock_products = int(low_stock_result)  # type: ignore[arg-type]

        # --- new customers ---
        if isinstance(new_cust_result, BaseException):
            logger.error("dashboard.new_customers unavailable", exc_info=new_cust_result)
            new_customers_30d = 0
            service_unavailable = True
        else:
            new_customers_30d = int(new_cust_result)  # type: ignore[arg-type]

        return DashboardDTO(
            revenue_30d=revenue_30d,
            orders_30d=orders_30d,
            new_customers_30d=new_customers_30d,
            low_stock_products=low_stock_products,
            pending_orders=pending_orders,
            pending_returns=pending_returns,
            recent_orders=recent_orders,
            service_unavailable=service_unavailable,
        )

    # ------------------------------------------------------------------
    # Sales Report
    # ------------------------------------------------------------------

    async def get_sales_report(
        self, from_date: date, to_date: date
    ) -> SalesReportDTO:
        """Assemble a sales report for the requested date window.

        Raises:
            ValueError: if the date range exceeds 365 days.
        """
        delta = (to_date - from_date).days
        if delta < 0:
            raise ValueError("from_date must be before or equal to to_date")
        if delta > _MAX_REPORT_DAYS:
            raise ValueError(
                f"Date range must not exceed {_MAX_REPORT_DAYS} days (requested {delta})"
            )

        report_task = self._order.get_sales_report(from_date, to_date)
        top_products_task = self._order.get_top_products(from_date, to_date, limit=10)
        category_task = self._order.get_category_revenue(from_date, to_date)
        status_task = self._order.get_order_status_breakdown(from_date, to_date)

        results = await asyncio.gather(
            report_task,
            top_products_task,
            category_task,
            status_task,
            return_exceptions=True,
        )

        report_result, top_result, category_result, status_result = results
        service_unavailable = False

        # --- core report ---
        if isinstance(report_result, BaseException):
            logger.error("sales_report.core unavailable", exc_info=report_result)
            total_revenue = Decimal("0")
            total_orders = 0
            revenue_by_day: list[RevenueDayDTO] = []
            service_unavailable = True
        else:
            report_dict: dict[str, Any] = report_result  # type: ignore[assignment]
            total_revenue = Decimal(str(report_dict.get("total_revenue", "0")))
            total_orders = int(report_dict.get("total_orders", 0))
            revenue_by_day = [
                RevenueDayDTO(
                    date=str(item["date"]),
                    revenue=Decimal(str(item.get("revenue", "0"))),
                    order_count=int(item.get("order_count", 0)),
                )
                for item in report_dict.get("revenue_by_day", [])
            ]

        # --- top products ---
        if isinstance(top_result, BaseException):
            logger.error("sales_report.top_products unavailable", exc_info=top_result)
            top_products: list[TopProductDTO] = []
            service_unavailable = True
        else:
            raw_top: list[dict[str, Any]] = top_result  # type: ignore[assignment]
            top_products = [
                TopProductDTO(
                    product_id=UUID(str(p["product_id"])),
                    product_name=str(p["product_name"]),
                    units_sold=int(p.get("units_sold", 0)),
                    revenue=Decimal(str(p.get("revenue", "0"))),
                )
                for p in raw_top
            ]

        # --- category revenue ---
        if isinstance(category_result, BaseException):
            logger.error("sales_report.category_revenue unavailable", exc_info=category_result)
            category_revenue: list[CategoryRevenueDTO] = []
            service_unavailable = True
        else:
            raw_cat: list[dict[str, Any]] = category_result  # type: ignore[assignment]
            category_revenue = [
                CategoryRevenueDTO(
                    category_name=str(c["category_name"]),
                    category_type=str(c["category_type"]),
                    revenue=Decimal(str(c.get("revenue", "0"))),
                )
                for c in raw_cat
            ]

        # --- status breakdown ---
        if isinstance(status_result, BaseException):
            logger.error("sales_report.status_breakdown unavailable", exc_info=status_result)
            order_status_breakdown: dict[str, int] = {}
            service_unavailable = True
        else:
            raw_status: dict[str, Any] = status_result  # type: ignore[assignment]
            order_status_breakdown = {k: int(v) for k, v in raw_status.items()}

        return SalesReportDTO(
            from_date=from_date.isoformat(),
            to_date=to_date.isoformat(),
            total_revenue=total_revenue,
            total_orders=total_orders,
            revenue_by_day=revenue_by_day,
            top_products=top_products,
            category_revenue=category_revenue,
            order_status_breakdown=order_status_breakdown,
            service_unavailable=service_unavailable,
        )

    # ------------------------------------------------------------------
    # Customers
    # ------------------------------------------------------------------

    async def list_customers(
        self, page: int, page_size: int
    ) -> PagedCustomerListDTO:
        """Return a paginated customer list sourced from the Auth Service."""
        raw = await self._auth.list_customers(page=page, page_size=page_size)
        items = [_parse_customer(u) for u in raw.get("items", [])]
        total_count = int(raw.get("total_count", len(items)))
        return PagedCustomerListDTO(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
        )

    async def get_customer_detail(self, user_id: UUID) -> CustomerDetailDTO:
        """Return a customer profile plus full order history (parallel fetch)."""
        user_task = self._auth.get_customer(user_id)
        orders_task = self._order.get_orders_by_user(user_id)

        user_result, orders_result = await asyncio.gather(
            user_task, orders_task, return_exceptions=True
        )

        if isinstance(user_result, BaseException):
            logger.error(
                "get_customer_detail.user unavailable",
                user_id=str(user_id),
                exc_info=user_result,
            )
            raise user_result  # customer must exist — propagate

        raw_user: dict[str, Any] = user_result  # type: ignore[assignment]

        if isinstance(orders_result, BaseException):
            logger.warning(
                "get_customer_detail.orders unavailable",
                user_id=str(user_id),
                exc_info=orders_result,
            )
            orders: list[OrderSummaryDTO] = []
        else:
            raw_orders: list[dict[str, Any]] = orders_result  # type: ignore[assignment]
            orders = [_parse_order(o) for o in raw_orders]

        user = _parse_customer(raw_user, total_orders=len(orders))
        return CustomerDetailDTO(user=user, orders=orders)
