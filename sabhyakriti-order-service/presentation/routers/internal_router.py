"""Internal service-to-service endpoints (require X-Internal-Secret header)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from application.dtos.order_dtos import (
    ConfirmOrderRequest,
    OrderDTO,
    VerifiedPurchaseResponse,
)
from application.services.order_application_service import OrderApplicationService
from presentation.dependencies import get_order_service, verify_internal_secret

router = APIRouter(
    prefix="/internal/v1",
    tags=["Internal"],
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
