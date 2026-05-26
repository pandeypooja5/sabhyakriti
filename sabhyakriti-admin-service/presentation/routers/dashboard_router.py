"""Admin dashboard and sales report endpoints."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from application.dtos.admin_dtos import DashboardDTO, SalesReportDTO
from application.services.admin_application_service import AdminApplicationService
from presentation.dependencies import get_admin_service, require_admin

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin-dashboard"],
)

AdminUser = Annotated[dict[str, Any], Depends(require_admin)]
AdminService = Annotated[AdminApplicationService, Depends(get_admin_service)]


@router.get(
    "/dashboard",
    response_model=DashboardDTO,
    summary="Admin dashboard KPIs (last 30 rolling days)",
)
async def get_dashboard(
    _: AdminUser,
    service: AdminService,
) -> DashboardDTO:
    """Return revenue, order counts, customer metrics, low-stock products,
    and recent orders for the admin dashboard.

    If one or more downstream services are unavailable the response still
    returns with available data and ``service_unavailable: true``.
    """
    return await service.get_dashboard()


@router.get(
    "/reports/sales",
    response_model=SalesReportDTO,
    summary="Sales report for a custom date range (max 365 days)",
)
async def get_sales_report(
    _: AdminUser,
    service: AdminService,
    from_date: Annotated[date, Query(description="Start date (inclusive) YYYY-MM-DD")],
    to_date: Annotated[date, Query(description="End date (inclusive) YYYY-MM-DD")],
) -> SalesReportDTO:
    """Return a detailed sales report including daily revenue, top products,
    category breakdown, and order status breakdown.

    The date range is capped at 365 days.
    """
    try:
        return await service.get_sales_report(from_date, to_date)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
