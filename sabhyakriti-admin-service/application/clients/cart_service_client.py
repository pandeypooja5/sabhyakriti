"""Async HTTP client for the Cart microservice (coupon admin proxy)."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)


class CartServiceClient:
    """Encapsulates all HTTP calls to the Cart Service.

    For the admin service this is exclusively used as a transparent proxy
    for coupon management endpoints.
    """

    def __init__(
        self,
        base_url: str,
        internal_secret: str,
        http_client: httpx.AsyncClient,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._internal_secret = internal_secret
        self._client = http_client

    # ------------------------------------------------------------------
    # Generic proxy (admin JWT pass-through)
    # ------------------------------------------------------------------

    async def proxy_request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Forward an admin request to the Cart Service unchanged."""
        url = f"{self._base_url}{path}"
        response = await self._client.request(method, url, **kwargs)
        return response
