"""HTTP client for communicating with the Order Service."""
from __future__ import annotations

import structlog
from uuid import UUID

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)

_TIMEOUT_SECONDS = 2.0
_MAX_RETRIES = 1


class OrderServiceClient:
    """Async HTTP client that calls the Order Service internal API."""

    def __init__(self, base_url: str, internal_secret: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._internal_secret = internal_secret
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=_TIMEOUT_SECONDS,
                headers={"X-Internal-Secret": self._internal_secret},
            )
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(_MAX_RETRIES + 1),
        wait=wait_exponential(multiplier=0.1, min=0.1, max=0.5),
        reraise=False,
    )
    async def is_verified_purchase(
        self, user_id: UUID, product_id: UUID
    ) -> bool | None:
        """Check whether a user has a verified purchase for a product.

        Returns:
            True / False from the Order Service, or None if unreachable
            (fail-open: treat as non-verified but do not block review).
        """
        try:
            client = await self._get_client()
            response = await client.get(
                "/internal/v1/orders/verified-purchase",
                params={"user_id": str(user_id), "product_id": str(product_id)},
            )
            response.raise_for_status()
            data: dict = response.json()  # type: ignore[type-arg]
            return bool(data.get("is_verified_purchase", False))
        except httpx.TimeoutException:
            logger.warning(
                "order_service_timeout",
                user_id=str(user_id),
                product_id=str(product_id),
            )
            return None
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "order_service_http_error",
                status_code=exc.response.status_code,
                user_id=str(user_id),
                product_id=str(product_id),
            )
            return None
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "order_service_unreachable",
                error=str(exc),
                user_id=str(user_id),
                product_id=str(product_id),
            )
            return None
