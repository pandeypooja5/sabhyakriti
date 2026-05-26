"""Async HTTP client for the Auth microservice."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import httpx
import structlog

logger = structlog.get_logger(__name__)


class AuthServiceClient:
    """Encapsulates all HTTP calls to the Auth Service."""

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

    async def get_new_customers_count(self, since: datetime) -> int:
        """Return the number of customers registered on or after *since*."""
        try:
            response = await self._client.get(
                f"{self._base_url}/internal/admin/new-customers-count",
                params={"since": since.isoformat()},
                headers=self._internal_headers(),
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            count: int = int(payload.get("count", 0))
            return count
        except httpx.HTTPError as exc:
            logger.warning("auth_service.get_new_customers_count failed", error=str(exc))
            raise

    async def list_customers(self, page: int, page_size: int) -> dict[str, Any]:
        """Return a paginated list of customer records."""
        try:
            response = await self._client.get(
                f"{self._base_url}/internal/admin/customers",
                params={"page": page, "page_size": page_size},
                headers=self._internal_headers(),
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data
        except httpx.HTTPError as exc:
            logger.warning("auth_service.list_customers failed", error=str(exc))
            raise

    async def get_customer(self, user_id: UUID) -> dict[str, Any]:
        """Return a single customer record by user_id."""
        try:
            response = await self._client.get(
                f"{self._base_url}/internal/admin/customers/{user_id}",
                headers=self._internal_headers(),
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data
        except httpx.HTTPError as exc:
            logger.warning(
                "auth_service.get_customer failed",
                user_id=str(user_id),
                error=str(exc),
            )
            raise
