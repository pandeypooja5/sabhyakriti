"""Admin-only order management endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from application.dtos.order_dtos import (
    OrderDTO,
    PagedOrderListDTO,
    ProcessReturnRequest,
    ReturnRequestDTO,
    UpdateOrderStatusRequest,
)
from application.services.order_application_service import OrderApplicationService
from presentation.dependencies import (
    CurrentUser,
    get_order_service,
    require_admin,
)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin - Orders"])


@router.get("/orders", response_model=PagedOrderListDTO)
async def admin_list_orders(
    admin_user: Annotated[CurrentUser, Depends(require_admin)],
    order_svc: Annotated[OrderApplicationService, Depends(get_order_service)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
) -> PagedOrderListDTO:
    """List all orders with optional status filter (admin)."""
    return await order_svc.admin_list_orders(
        page=page,
        page_size=page_size,
        status=status,
    )


@router.patch("/orders/{order_id}/status", response_model=OrderDTO)
async def update_order_status(
    order_id: UUID,
    body: UpdateOrderStatusRequest,
    admin_user: Annotated[CurrentUser, Depends(require_admin)],
    order_svc: Annotated[OrderApplicationService, Depends(get_order_service)],
) -> OrderDTO:
    """Update an order's status (CONFIRMED→SHIPPED or SHIPPED→DELIVERED)."""
    return await order_svc.update_order_status(
        order_id=order_id,
        request=body,
    )


@router.post("/returns/{return_id}/process", response_model=ReturnRequestDTO)
async def process_return(
    return_id: UUID,
    body: ProcessReturnRequest,
    admin_user: Annotated[CurrentUser, Depends(require_admin)],
    order_svc: Annotated[OrderApplicationService, Depends(get_order_service)],
) -> ReturnRequestDTO:
    """Approve or reject a pending return request."""
    return await order_svc.process_return(
        return_request_id=return_id,
        admin_user_id=admin_user.user_id,
        request=body,
    )


@router.post("/returns/{return_id}/initiate-refund", response_model=ReturnRequestDTO)
async def initiate_refund(
    return_id: UUID,
    admin_user: Annotated[CurrentUser, Depends(require_admin)],
    order_svc: Annotated[OrderApplicationService, Depends(get_order_service)],
) -> ReturnRequestDTO:
    """Mark return items received and initiate refund via Payment Service."""
    return await order_svc.initiate_return_refund(
        return_request_id=return_id,
        admin_user_id=admin_user.user_id,
    )
