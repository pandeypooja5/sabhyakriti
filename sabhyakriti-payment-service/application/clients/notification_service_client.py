"""Async HTTP client for the Notification Service.

Notification calls are fire-and-forget — failures are logged but never
propagated to the caller so that a notification outage cannot break
the payment flow.
"""

from __future__ import annotations

from uuid import UUID

import httpx
import structlog

from application.dtos.payment_dtos import PaymentDTO

logger = structlog.get_logger(__name__)


class NotificationServiceClient:
    """Thin async wrapper around the Notification Service internal API."""

    def __init__(self, base_url: str, internal_secret: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {
            "X-Internal-Secret": internal_secret,
            "Content-Type": "application/json",
        }

    async def send_payment_receipt(
        self,
        order_id: UUID,
        payment: PaymentDTO,
    ) -> None:
        """Send a payment receipt notification — fire and forget.

        Any exception is caught and logged, never re-raised, so that a
        notification failure cannot affect the payment confirmation flow.
        """
        url = f"{self._base_url}/internal/v1/notifications/payment-receipt"
        payload = {
            "order_id": str(order_id),
            "payment_id": str(payment.payment_id),
            "razorpay_payment_id": payment.razorpay_payment_id,
            "method": payment.method,
            "amount": str(payment.amount),
            "captured_at": payment.captured_at.isoformat() if payment.captured_at else None,
            "status": payment.status,
        }
        log = logger.bind(order_id=str(order_id), payment_id=str(payment.payment_id))
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(url, headers=self._headers, json=payload)
                response.raise_for_status()
            log.info("payment_receipt_notification_sent")
        except Exception as exc:  # noqa: BLE001
            log.warning("payment_receipt_notification_failed", error=str(exc))
