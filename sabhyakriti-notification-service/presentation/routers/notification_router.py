"""
All 13 internal notification endpoints.

Every endpoint:
1. Validates the X-Internal-Secret header (via dependency).
2. Accepts the request body.
3. Enqueues the send operation as a FastAPI BackgroundTask (fire-and-forget).
4. Returns HTTP 202 Accepted immediately.

The background task calls the application service which never raises to its
caller — all errors are silently logged to structlog/CloudWatch.
"""

from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse

from application.dtos.notification_dtos import (
    EmailVerificationRequest,
    OrderCancelledRequest,
    OrderConfirmationRequest,
    OrderDeliveredRequest,
    OrderDeliveredSMSRequest,
    OrderShippedRequest,
    OrderShippedSMSRequest,
    OTPSMSRequest,
    PaymentReceiptRequest,
    PasswordResetRequest,
    RefundProcessedRequest,
    ReturnApprovedRequest,
    ReturnReceivedRequest,
)
from application.services.notification_application_service import NotificationApplicationService
from presentation.dependencies import get_notification_service, verify_internal_secret

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/internal/v1/notifications",
    tags=["notifications"],
    dependencies=[Depends(verify_internal_secret)],
)

_ACCEPTED = JSONResponse(
    status_code=status.HTTP_202_ACCEPTED,
    content={"status": "accepted"},
)


# ── Email Endpoints ────────────────────────────────────────────────────────────


@router.post(
    "/email/verification",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send email verification",
)
async def send_email_verification(
    body: EmailVerificationRequest,
    background_tasks: BackgroundTasks,
    svc: Annotated[NotificationApplicationService, Depends(get_notification_service)],
) -> JSONResponse:
    """Enqueue an email-verification notification. Returns 202 immediately."""
    background_tasks.add_task(svc.send_email_verification, body)
    return _ACCEPTED


@router.post(
    "/email/password-reset",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send password reset email",
)
async def send_password_reset(
    body: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    svc: Annotated[NotificationApplicationService, Depends(get_notification_service)],
) -> JSONResponse:
    """Enqueue a password-reset notification. Returns 202 immediately."""
    background_tasks.add_task(svc.send_password_reset, body)
    return _ACCEPTED


@router.post(
    "/email/order-confirmation",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send order confirmation email",
)
async def send_order_confirmation(
    body: OrderConfirmationRequest,
    background_tasks: BackgroundTasks,
    svc: Annotated[NotificationApplicationService, Depends(get_notification_service)],
) -> JSONResponse:
    """Enqueue an order-confirmation notification. Returns 202 immediately."""
    background_tasks.add_task(svc.send_order_confirmation, body)
    return _ACCEPTED


@router.post(
    "/email/order-shipped",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send order shipped email (+ optional SMS)",
)
async def send_order_shipped(
    body: OrderShippedRequest,
    background_tasks: BackgroundTasks,
    svc: Annotated[NotificationApplicationService, Depends(get_notification_service)],
) -> JSONResponse:
    """Enqueue an order-shipped notification. Returns 202 immediately."""
    background_tasks.add_task(svc.send_order_shipped, body)
    return _ACCEPTED


@router.post(
    "/email/order-delivered",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send order delivered email (+ optional SMS)",
)
async def send_order_delivered(
    body: OrderDeliveredRequest,
    background_tasks: BackgroundTasks,
    svc: Annotated[NotificationApplicationService, Depends(get_notification_service)],
) -> JSONResponse:
    """Enqueue an order-delivered notification. Returns 202 immediately."""
    background_tasks.add_task(svc.send_order_delivered, body)
    return _ACCEPTED


@router.post(
    "/email/order-cancelled",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send order cancelled email",
)
async def send_order_cancelled(
    body: OrderCancelledRequest,
    background_tasks: BackgroundTasks,
    svc: Annotated[NotificationApplicationService, Depends(get_notification_service)],
) -> JSONResponse:
    """Enqueue an order-cancellation notification. Returns 202 immediately."""
    background_tasks.add_task(svc.send_order_cancelled, body)
    return _ACCEPTED


@router.post(
    "/email/return-received",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send return received email",
)
async def send_return_received(
    body: ReturnReceivedRequest,
    background_tasks: BackgroundTasks,
    svc: Annotated[NotificationApplicationService, Depends(get_notification_service)],
) -> JSONResponse:
    """Enqueue a return-received notification. Returns 202 immediately."""
    background_tasks.add_task(svc.send_return_received, body)
    return _ACCEPTED


@router.post(
    "/email/return-approved",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send return approved email",
)
async def send_return_approved(
    body: ReturnApprovedRequest,
    background_tasks: BackgroundTasks,
    svc: Annotated[NotificationApplicationService, Depends(get_notification_service)],
) -> JSONResponse:
    """Enqueue a return-approved notification. Returns 202 immediately."""
    background_tasks.add_task(svc.send_return_approved, body)
    return _ACCEPTED


@router.post(
    "/email/refund-processed",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send refund processed email",
)
async def send_refund_processed(
    body: RefundProcessedRequest,
    background_tasks: BackgroundTasks,
    svc: Annotated[NotificationApplicationService, Depends(get_notification_service)],
) -> JSONResponse:
    """Enqueue a refund-processed notification. Returns 202 immediately."""
    background_tasks.add_task(svc.send_refund_processed, body)
    return _ACCEPTED


@router.post(
    "/email/payment-receipt",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send payment receipt email",
)
async def send_payment_receipt(
    body: PaymentReceiptRequest,
    background_tasks: BackgroundTasks,
    svc: Annotated[NotificationApplicationService, Depends(get_notification_service)],
) -> JSONResponse:
    """Enqueue a payment-receipt notification. Returns 202 immediately."""
    background_tasks.add_task(svc.send_payment_receipt, body)
    return _ACCEPTED


# ── SMS Endpoints ──────────────────────────────────────────────────────────────


@router.post(
    "/sms/otp",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send OTP via SMS",
)
async def send_otp_sms(
    body: OTPSMSRequest,
    background_tasks: BackgroundTasks,
    svc: Annotated[NotificationApplicationService, Depends(get_notification_service)],
) -> JSONResponse:
    """Enqueue an OTP SMS. Returns 202 immediately."""
    background_tasks.add_task(svc.send_otp_sms, body)
    return _ACCEPTED


@router.post(
    "/sms/order-shipped",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send order shipped SMS",
)
async def send_order_shipped_sms(
    body: OrderShippedSMSRequest,
    background_tasks: BackgroundTasks,
    svc: Annotated[NotificationApplicationService, Depends(get_notification_service)],
) -> JSONResponse:
    """Enqueue an order-shipped SMS. Returns 202 immediately."""
    background_tasks.add_task(svc.send_order_shipped_sms, body)
    return _ACCEPTED


@router.post(
    "/sms/order-delivered",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send order delivered SMS",
)
async def send_order_delivered_sms(
    body: OrderDeliveredSMSRequest,
    background_tasks: BackgroundTasks,
    svc: Annotated[NotificationApplicationService, Depends(get_notification_service)],
) -> JSONResponse:
    """Enqueue an order-delivered SMS. Returns 202 immediately."""
    background_tasks.add_task(svc.send_order_delivered_sms, body)
    return _ACCEPTED
