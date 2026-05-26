"""Internal API endpoints — only reachable via service-to-service calls.

All routes require the ``X-Internal-Secret`` header.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from application.dtos.payment_dtos import CODConfirmRequest, PaymentDTO, RefundDTO, RefundRequest
from application.services.payment_application_service import PaymentApplicationService
from presentation.dependencies import get_payment_service, verify_internal_secret

router = APIRouter(
    prefix="/internal/v1/payments",
    tags=["Internal"],
    dependencies=[Depends(verify_internal_secret)],
)


# ---------------------------------------------------------------------------
# Flow 3 — Confirm COD payment (called by Order Service)
# ---------------------------------------------------------------------------


@router.post(
    "/cod-confirm",
    response_model=PaymentDTO,
    status_code=status.HTTP_201_CREATED,
    summary="[INTERNAL] Confirm a Cash-on-Delivery payment",
)
async def confirm_cod_payment(
    body: CODConfirmRequest,
    service: Annotated[PaymentApplicationService, Depends(get_payment_service)],
) -> PaymentDTO:
    """Create a COD payment record with status=CAPTURED immediately.

    Called by the Order Service when an order is placed with COD.
    No Razorpay API call is made.
    """
    try:
        return await service.confirm_cod_payment(body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Flow 5 — Initiate refund (called by Order Service)
# ---------------------------------------------------------------------------


@router.post(
    "/{order_id}/refund",
    response_model=RefundDTO,
    status_code=status.HTTP_200_OK,
    summary="[INTERNAL] Initiate a refund for a captured payment",
)
async def initiate_refund(
    order_id: UUID,
    body: RefundRequest,
    service: Annotated[PaymentApplicationService, Depends(get_payment_service)],
) -> RefundDTO:
    """Initiate a Razorpay refund for a captured payment.

    The ``order_id`` in the path must match ``body.order_id``.
    """
    if body.order_id != order_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path order_id and body order_id must match.",
        )
    try:
        return await service.initiate_refund(body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
