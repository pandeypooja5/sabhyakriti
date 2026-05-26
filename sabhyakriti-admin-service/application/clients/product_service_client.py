"""Async HTTP client for the Product microservice."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)


class ProductServiceClient:
    """Encapsulates all HTTP calls to the Product Service."""

    def __init__(
        self,
        base_url: str,
        internal_secret: str,
        http_client: httpx.AsyncClient,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._internal_secret = internal_secret
        self._client = http_client

    def _internal_headers(self) -> dict[str, str]:
        return {"X-Internal-Secret": self._internal_secret}

    async def get_low_stock_count(self, threshold: int = 5) -> int:
        """Return the number of product variants with stock <= *threshold*."""
        try:
            response = await self._client.get(
                f"{self._base_url}/internal/admin/low-stock-count",
                params={"threshold": threshold},
                headers=self._internal_headers(),
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            count: int = int(payload.get("count", 0))
            return count
        except httpx.HTTPError as exc:
            logger.warning("product_service.get_low_stock_count failed", error=str(exc))
            raise

    # ------------------------------------------------------------------
    # Generic proxy (admin JWT pass-through)
    # ------------------------------------------------------------------

    async def proxy_request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Forward an admin request to the Product Service unchanged."""
        url = f"{self._base_url}{path}"
        response = await self._client.request(method, url, **kwargs)
        return response
