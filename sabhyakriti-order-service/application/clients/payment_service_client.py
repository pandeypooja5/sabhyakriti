"""HTTP client for the Payment microservice."""

from __future__ import annotations

from decimal import Decimal

import structlog
from httpx import AsyncClient, RequestError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = structlog.get_logger(__name__)


class PaymentServiceClient:
    """Async HTTP client wrapping the Payment Service API."""

    def __init__(self, base_url: str, internal_secret: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._internal_secret = internal_secret

    def _headers(self) -> dict[str, str]:
        return {
            "X-Internal-Secret": self._internal_secret,
            "Content-Type": "application/json",
        }

    @retry(
        retry=retry_if_exception_type(RequestError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
    )
    async def initiate_refund(
        self,
        order_id: str,
        amount: Decimal,
        reason: str = "order_cancelled",
    ) -> dict[str, object]:
        """Initiate a refund for the given order and return the refund record."""
        async with AsyncClient(base_url=self._base_url, timeout=15.0) as client:
            response = await client.post(
                "/internal/v1/refunds",
                json={
                    "order_id": order_id,
                    "amount": str(amount),
                    "reason": reason,
                },
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]

    @retry(
        retry=retry_if_exception_type(RequestError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
    )
    async def cancel_pending_payment(self, order_id: str) -> None:
        """Cancel a payment that was initiated but not yet confirmed."""
        async with AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            response = await client.post(
                f"/internal/v1/payments/cancel",
                json={"order_id": order_id},
                headers=self._headers(),
            )
            response.raise_for_status()
