"""
HTTP client for the Notification microservice.

All notification calls are fire-and-forget: they are submitted as background
tasks and any failure is only logged, never propagated to the caller.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from uuid import UUID

import structlog
from httpx import AsyncClient

logger = structlog.get_logger(__name__)


class NotificationServiceClient:
    """Async HTTP client wrapping the Notification Service API."""

    def __init__(self, base_url: str, internal_secret: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._internal_secret = internal_secret

    def _headers(self) -> dict[str, str]:
        return {
            "X-Internal-Secret": self._internal_secret,
            "Content-Type": "application/json",
        }

    async def _post(self, path: str, payload: dict[str, object]) -> None:
        """Internal fire-and-forget POST; all errors are swallowed."""
        try:
            async with AsyncClient(
                base_url=self._base_url, timeout=5.0
            ) as client:
                response = await client.post(
                    path, json=payload, headers=self._headers()
                )
                response.raise_for_status()
        except Exception:
            logger.exception("notification_failed", path=path, payload=payload)

    def _fire(self, path: str, payload: dict[str, object]) -> None:
        """Schedule the notification as a background asyncio task."""
        asyncio.create_task(self._post(path, payload))  # noqa: RUF006

    # ------------------------------------------------------------------
    # Domain notification methods
    # ------------------------------------------------------------------

    def notify_order_placed(
        self,
        user_id: str,
        order_id: str,
        order_number: str,
        total_amount: Decimal,
    ) -> None:
        self._fire(
            "/internal/v1/notifications/order-placed",
            {
                "user_id": user_id,
                "order_id": order_id,
                "order_number": order_number,
                "total_amount": str(total_amount),
            },
        )

    def notify_order_confirmed(
        self,
        user_id: str,
        order_id: str,
        order_number: str,
    ) -> None:
        self._fire(
            "/internal/v1/notifications/order-confirmed",
            {
                "user_id": user_id,
                "order_id": order_id,
                "order_number": order_number,
            },
        )

    def notify_order_shipped(
        self,
        user_id: str,
        order_id: str,
        order_number: str,
    ) -> None:
        self._fire(
            "/internal/v1/notifications/order-shipped",
            {
                "user_id": user_id,
                "order_id": order_id,
                "order_number": order_number,
            },
        )

    def notify_order_delivered(
        self,
        user_id: str,
        order_id: str,
        order_number: str,
    ) -> None:
        self._fire(
            "/internal/v1/notifications/order-delivered",
            {
                "user_id": user_id,
                "order_id": order_id,
                "order_number": order_number,
            },
        )

    def notify_order_cancelled(
        self,
        user_id: str,
        order_id: str,
        order_number: str,
        reason: str,
    ) -> None:
        self._fire(
            "/internal/v1/notifications/order-cancelled",
            {
                "user_id": user_id,
                "order_id": order_id,
                "order_number": order_number,
                "reason": reason,
            },
        )

    def notify_return_submitted(
        self,
        user_id: str,
        order_id: str,
        return_request_id: str,
    ) -> None:
        self._fire(
            "/internal/v1/notifications/return-submitted",
            {
                "user_id": user_id,
                "order_id": order_id,
                "return_request_id": return_request_id,
            },
        )

    def notify_return_approved(
        self,
        user_id: str,
        order_id: str,
        return_request_id: str,
    ) -> None:
        self._fire(
            "/internal/v1/notifications/return-approved",
            {
                "user_id": user_id,
                "order_id": order_id,
                "return_request_id": return_request_id,
            },
        )

    def notify_return_rejected(
        self,
        user_id: str,
        order_id: str,
        return_request_id: str,
        admin_notes: str | None,
    ) -> None:
        self._fire(
            "/internal/v1/notifications/return-rejected",
            {
                "user_id": user_id,
                "order_id": order_id,
                "return_request_id": return_request_id,
                "admin_notes": admin_notes or "",
            },
        )

    def notify_refund_initiated(
        self,
        user_id: str,
        order_id: str,
        refund_amount: Decimal,
    ) -> None:
        self._fire(
            "/internal/v1/notifications/refund-initiated",
            {
                "user_id": user_id,
                "order_id": order_id,
                "refund_amount": str(refund_amount),
            },
        )
