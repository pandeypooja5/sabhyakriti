"""Async HTTP client for the Order Service.

Uses httpx with tenacity retry logic (3 attempts, exponential back-off)
for resilience against transient network failures.
"""

from __future__ import annotations

from uuid import UUID

import httpx
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class OrderServiceClient:
    """Thin async wrapper around the Order Service internal API."""

    def __init__(self, base_url: str, internal_secret: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {
            "X-Internal-Secret": internal_secret,
            "Content-Type": "application/json",
        }

    @retry(
        retry=retry_if_exception_type(httpx.TransportError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def confirm_order(
        self,
        order_id: UUID,
        payment_reference: str,
        payment_method: str = "RAZORPAY",
    ) -> None:
        """Notify the Order Service that a payment was captured successfully.

        Calls the order service ``/confirm`` endpoint which transitions the
        order PENDING -> CONFIRMED and records the payment reference.
        """
        url = f"{self._base_url}/internal/v1/orders/{order_id}/confirm"
        log = logger.bind(order_id=str(order_id))
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                headers=self._headers,
                json={
                    "payment_reference": payment_reference,
                    "payment_method": payment_method,
                },
            )
            response.raise_for_status()
        log.info("order_confirmed")

    @retry(
        retry=retry_if_exception_type(httpx.TransportError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def cancel_order(self, order_id: UUID, reason: str) -> None:
        """Notify the Order Service to cancel an order due to payment failure/timeout."""
        url = f"{self._base_url}/internal/v1/orders/{order_id}/cancel"
        log = logger.bind(order_id=str(order_id), reason=reason)
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                headers=self._headers,
                json={"reason": reason},
            )
            response.raise_for_status()
        log.info("order_cancelled")

    @retry(
        retry=retry_if_exception_type(httpx.TransportError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_order_user_id(self, order_id: UUID) -> UUID:
        """Fetch the user ID who owns an order (used for IDOR check)."""
        url = f"{self._base_url}/internal/v1/orders/{order_id}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=self._headers)
            response.raise_for_status()
            data = response.json()
        return UUID(data["user_id"])

    @retry(
        retry=retry_if_exception_type(httpx.TransportError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_order_number(self, order_id: UUID) -> str:
        """Fetch the human-readable order number for receipt generation."""
        url = f"{self._base_url}/internal/v1/orders/{order_id}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=self._headers)
            response.raise_for_status()
            data = response.json()
        return str(data.get("order_number", str(order_id)))
