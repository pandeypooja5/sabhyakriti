"""HTTP client for the Product microservice."""

from __future__ import annotations

import structlog
from httpx import AsyncClient, RequestError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = structlog.get_logger(__name__)


class ProductServiceClient:
    """Async HTTP client wrapping the Product Service API."""

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
    async def reserve_stock(
        self,
        product_id: str,
        variant_id: str | None,
        delta: int,
    ) -> None:
        """
        Reserve *delta* units of stock for *product_id* / *variant_id*.

        Raises HTTPStatusError on failure (e.g. 409 insufficient stock).
        """
        async with AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            payload: dict[str, object] = {
                "product_id": product_id,
                "delta": delta,
            }
            if variant_id:
                payload["variant_id"] = variant_id
            response = await client.post(
                "/internal/v1/stock/reserve",
                json=payload,
                headers=self._headers(),
            )
            response.raise_for_status()

    @retry(
        retry=retry_if_exception_type(RequestError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
    )
    async def release_stock(
        self,
        product_id: str,
        variant_id: str | None,
        delta: int,
    ) -> None:
        """
        Release previously reserved stock (compensating transaction).

        Errors are logged but not re-raised to avoid masking the original error.
        """
        async with AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            try:
                payload: dict[str, object] = {
                    "product_id": product_id,
                    "delta": delta,
                }
                if variant_id:
                    payload["variant_id"] = variant_id
                response = await client.post(
                    "/internal/v1/stock/release",
                    json=payload,
                    headers=self._headers(),
                )
                response.raise_for_status()
            except Exception:
                logger.exception(
                    "stock_release_failed",
                    product_id=product_id,
                    variant_id=variant_id,
                    delta=delta,
                )
