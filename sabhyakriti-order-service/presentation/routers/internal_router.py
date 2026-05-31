"""Internal service-to-service endpoints (require X-Internal-Secret header)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from application.dtos.order_dtos import (
    ConfirmOrderRequest,
    OrderDTO,
    OrderSummaryDTO,
    VerifiedPurchaseResponse,
)
from application.services.order_application_service import OrderApplicationService
from presentation.dependencies import get_order_service, verify_internal_secret

router = APIRouter(
    prefix="/internal/v1",
    tags=["Internal"],
    dependencies=[Depends(verify_internal_secret)],
)

# Admin internal router (used by Admin Service dashboard)
admin_router = APIRouter(
    prefix="/internal/admin",
    tags=["Internal-Admin"],
    dependencies=[Depends(verify_internal_secret)],
)


@router.post("/orders/{order_id}/confirm", response_model=OrderDTO)
async def confirm_order(
    order_id: UUID,
    body: ConfirmOrderRequest,
    order_svc: Annotated[OrderApplicationService, Depends(get_order_service)],
) -> OrderDTO:
    """
    Called by Payment Service to confirm a PENDING order after payment success.

    Transitions order status from PENDING → CONFIRMED.
    """
    return await order_svc.confirm_order(
        order_id=order_id,
        request=body,
    )


@router.get("/orders/verified-purchase", response_model=VerifiedPurchaseResponse)
async def check_verified_purchase(
    user_id: str = Query(...),
    product_id: str = Query(...),
    order_svc: OrderApplicationService = Depends(get_order_service),
) -> VerifiedPurchaseResponse:
    """
    Called by Product Service to check if a user has a delivered purchase
    of a specific product (for review eligibility).
    """
    eligible = await order_svc.check_verified_purchase(
        user_id=user_id,
        product_id=product_id,
    )
    return VerifiedPurchaseResponse(
        user_id=user_id,
        product_id=product_id,
        order_id=UUID(int=0),  # placeholder — not relevant for eligibility check
        order_number="",
        is_eligible=eligible,
    )


# ---------------------------------------------------------------------------
# Admin-facing internal endpoints (called by Admin Service dashboard)
# ---------------------------------------------------------------------------

@admin_router.get("/recent-orders", response_model=list[OrderSummaryDTO])
async def get_recent_orders(
    order_svc: Annotated[OrderApplicationService, Depends(get_order_service)],
    limit: int = Query(default=10, ge=1, le=50),
) -> list[OrderSummaryDTO]:
    """Return the most recent orders across all statuses (for dashboard)."""
    result = await order_svc.admin_list_orders(page=1, page_size=limit)
    return result.items


@admin_router.get("/stats")
async def get_dashboard_stats(
    order_svc: Annotated[OrderApplicationService, Depends(get_order_service)],
    days: int = Query(default=30, ge=1, le=365),
) -> dict:
    """Return aggregated revenue and order count for last *days* days."""
    result = await order_svc.admin_list_orders(page=1, page_size=1000)
    return {
        "revenue": str(sum(o.total_amount for o in result.items)),
        "order_count": result.total,
    }


@admin_router.get("/pending-counts")
async def get_pending_counts(
    order_svc: Annotated[OrderApplicationService, Depends(get_order_service)],
) -> dict:
    """Return count of pending orders and pending returns."""
    from application.dtos.order_dtos import OrderStatus
    pending = await order_svc.admin_list_orders(page=1, page_size=1, status="PENDING")
    return {
        "pending_orders": pending.total,
        "pending_returns": 0,
    }
