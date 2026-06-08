"""Public-facing payment API endpoints.

Authentication:
- All routes (except webhook) require a valid Bearer JWT.
- The webhook route relies solely on Razorpay HMAC-SHA256 signature verification.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, status

from application.dtos.payment_dtos import (
    CreateOrderRequest,
    PaymentDTO,
    PaymentReceiptDTO,
    RazorpayOrderDTO,
    VerifyPaymentRequest,
)
from application.services.payment_application_service import PaymentApplicationService
from presentation.dependencies import TokenPayload, get_current_user, get_payment_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


# ---------------------------------------------------------------------------
# Flow 1 — Create Razorpay order
# ---------------------------------------------------------------------------


@router.post(
    "/create-order",
    response_model=RazorpayOrderDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Razorpay order to begin checkout",
)
async def create_order(
    body: CreateOrderRequest,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[PaymentApplicationService, Depends(get_payment_service)],
) -> RazorpayOrderDTO:
    """Create a Razorpay order and return the order details needed to open the
    Razorpay checkout modal on the frontend.

    Enforces a max-3-attempts / 30-minute window rate limit per order.
    """
    try:
        return await service.create_razorpay_order(
            order_id=body.order_id,
            user_id=current_user.user_id,
            amount=body.amount,
            currency=body.currency,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Flow 2 — Verify payment after Razorpay callback
# ---------------------------------------------------------------------------


@router.post(
    "/verify",
    response_model=PaymentDTO,
    status_code=status.HTTP_200_OK,
    summary="Verify payment signature after Razorpay checkout",
)
async def verify_payment(
    body: VerifyPaymentRequest,
    background_tasks: BackgroundTasks,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[PaymentApplicationService, Depends(get_payment_service)],
) -> PaymentDTO:
    """Verify the HMAC-SHA256 signature from Razorpay checkout and capture the payment.

    On success, a payment receipt email is sent asynchronously via the
    Notification Service.
    """
    try:
        payment_dto = await service.verify_payment(body)
    except ValueError as exc:
        # Check if it's an idempotent "already captured" case
        if "already captured" in str(exc).lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    # Fire-and-forget notification
    background_tasks.add_task(
        service._notification_client.send_payment_receipt,  # noqa: SLF001
        body.order_id,
        payment_dto,
    )
    return payment_dto


# ---------------------------------------------------------------------------
# Flow 6 — Get payment receipt
# ---------------------------------------------------------------------------


@router.get(
    "/{order_id}/receipt",
    response_model=PaymentReceiptDTO,
    status_code=status.HTTP_200_OK,
    summary="Get payment receipt for an order",
)
async def get_payment_receipt(
    order_id: UUID,
    current_user: Annotated[TokenPayload, Depends(get_current_user)],
    service: Annotated[PaymentApplicationService, Depends(get_payment_service)],
) -> PaymentReceiptDTO:
    """Return the payment receipt for the given order.

    An IDOR check ensures the requesting user owns the order.
    """
    try:
        return await service.get_payment_receipt(
            user_id=current_user.user_id,
            order_id=order_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Flow 4 — Razorpay webhook (NO JWT auth — signature only)
# ---------------------------------------------------------------------------


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Razorpay webhook endpoint",
    include_in_schema=False,  # Don't expose in public docs
)
async def razorpay_webhook(
    request: Request,
    service: Annotated[PaymentApplicationService, Depends(get_payment_service)],
    x_razorpay_signature: Annotated[str | None, Header()] = None,
    x_razorpay_event_id: Annotated[str | None, Header()] = None,
) -> dict:  # type: ignore[type-arg]
    """Receive and process Razorpay webhook events.

    Authentication is done exclusively via HMAC-SHA256 signature comparison
    of the raw request body against the ``X-Razorpay-Signature`` header.
    Duplicate events are silently ignored via the idempotency key.
    """
    if not x_razorpay_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Razorpay-Signature header.",
        )

    raw_body = await request.body()

    try:
        await service.process_webhook(raw_body, x_razorpay_signature, event_id=x_razorpay_event_id)
    except ValueError as exc:
        # Signature failures should return 400 to instruct Razorpay not to retry
        logger.warning("webhook_rejected", error=str(exc))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {"status": "ok"}
