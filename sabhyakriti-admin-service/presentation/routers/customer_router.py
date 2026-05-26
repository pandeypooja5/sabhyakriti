"""Admin customer management endpoints."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from application.dtos.admin_dtos import CustomerDetailDTO, PagedCustomerListDTO
from application.services.admin_application_service import AdminApplicationService
from presentation.dependencies import get_admin_service, require_admin

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin-customers"],
)

AdminUser = Annotated[dict[str, Any], Depends(require_admin)]
AdminService = Annotated[AdminApplicationService, Depends(get_admin_service)]


@router.get(
    "/customers",
    response_model=PagedCustomerListDTO,
    summary="List all customers (paginated)",
)
async def list_customers(
    _: AdminUser,
    service: AdminService,
    page: Annotated[int, Query(ge=1, description="Page number (1-based)")] = 1,
    page_size: Annotated[
        int, Query(ge=1, le=200, description="Items per page")
    ] = 20,
) -> PagedCustomerListDTO:
    """Return a paginated list of all registered customers."""
    return await service.list_customers(page=page, page_size=page_size)


@router.get(
    "/customers/{user_id}",
    response_model=CustomerDetailDTO,
    summary="Get customer profile + full order history",
)
async def get_customer_detail(
    user_id: UUID,
    _: AdminUser,
    service: AdminService,
) -> CustomerDetailDTO:
    """Return a single customer's profile and their complete order history.

    Both the user record and order history are fetched in parallel from the
    Auth and Order services respectively.
    """
    try:
        return await service.get_customer_detail(user_id)
    except Exception as exc:
        logger.warning(
            "get_customer_detail.not_found_or_error",
            user_id=str(user_id),
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {user_id} not found",
        ) from exc
