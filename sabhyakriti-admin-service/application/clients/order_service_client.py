"""Async HTTP client for the Order microservice."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any
from uuid import UUID

import httpx
import structlog

logger = structlog.get_logger(__name__)


class OrderServiceClient:
    """Encapsulates all HTTP calls to the Order Service."""

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
    # Internal-facing helpers (X-Internal-Secret auth)
    # ------------------------------------------------------------------

    def _internal_headers(self) -> dict[str, str]:
        return {"X-Internal-Secret": self._internal_secret}

    async def get_dashboard_stats(self, days: int = 30) -> dict[str, Any]:
        """Retrieve aggregated KPIs from the Order Service for the last *days* days."""
        try:
            response = await self._client.get(
                f"{self._base_url}/internal/admin/stats",
                params={"days": days},
                headers=self._internal_headers(),
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data
        except httpx.HTTPError as exc:
            logger.warning("order_service.get_dashboard_stats failed", error=str(exc))
            raise

    async def get_pending_counts(self) -> dict[str, Any]:
        """Return pending order count and pending return count."""
        try:
            response = await self._client.get(
                f"{self._base_url}/internal/admin/pending-counts",
                headers=self._internal_headers(),
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data
        except httpx.HTTPError as exc:
            logger.warning("order_service.get_pending_counts failed", error=str(exc))
            raise

    async def get_recent_orders(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return the *limit* most recent orders across all statuses."""
        try:
            response = await self._client.get(
                f"{self._base_url}/internal/admin/recent-orders",
                params={"limit": limit},
                headers=self._internal_headers(),
            )
            response.raise_for_status()
            data: list[dict[str, Any]] = response.json()
            return data
        except httpx.HTTPError as exc:
            logger.warning("order_service.get_recent_orders failed", error=str(exc))
            raise

    async def get_sales_report(
        self, from_date: date, to_date: date
    ) -> dict[str, Any]:
        """Retrieve sales aggregation data for a date range."""
        try:
            response = await self._client.get(
                f"{self._base_url}/internal/admin/sales-report",
                params={"from_date": from_date.isoformat(), "to_date": to_date.isoformat()},
                headers=self._internal_headers(),
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data
        except httpx.HTTPError as exc:
            logger.warning("order_service.get_sales_report failed", error=str(exc))
            raise

    async def get_top_products(
        self,
        from_date: date,
        to_date: date,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Return the top-selling products over the given date range."""
        try:
            response = await self._client.get(
                f"{self._base_url}/internal/admin/top-products",
                params={
                    "from_date": from_date.isoformat(),
                    "to_date": to_date.isoformat(),
                    "limit": limit,
                },
                headers=self._internal_headers(),
            )
            response.raise_for_status()
            data: list[dict[str, Any]] = response.json()
            return data
        except httpx.HTTPError as exc:
            logger.warning("order_service.get_top_products failed", error=str(exc))
            raise

    async def get_category_revenue(
        self,
        from_date: date,
        to_date: date,
    ) -> list[dict[str, Any]]:
        """Return revenue broken down by product category for the date range."""
        try:
            response = await self._client.get(
                f"{self._base_url}/internal/admin/category-revenue",
                params={
                    "from_date": from_date.isoformat(),
                    "to_date": to_date.isoformat(),
                },
                headers=self._internal_headers(),
            )
            response.raise_for_status()
            data: list[dict[str, Any]] = response.json()
            return data
        except httpx.HTTPError as exc:
            logger.warning("order_service.get_category_revenue failed", error=str(exc))
            raise

    async def get_order_status_breakdown(
        self,
        from_date: date,
        to_date: date,
    ) -> dict[str, Any]:
        """Return a mapping of order_status → count for the date range."""
        try:
            response = await self._client.get(
                f"{self._base_url}/internal/admin/order-status-breakdown",
                params={
                    "from_date": from_date.isoformat(),
                    "to_date": to_date.isoformat(),
                },
                headers=self._internal_headers(),
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data
        except httpx.HTTPError as exc:
            logger.warning(
                "order_service.get_order_status_breakdown failed", error=str(exc)
            )
            raise

    async def get_orders_by_user(self, user_id: UUID) -> list[dict[str, Any]]:
        """Return all orders placed by a specific user."""
        try:
            response = await self._client.get(
                f"{self._base_url}/internal/admin/users/{user_id}/orders",
                headers=self._internal_headers(),
            )
            response.raise_for_status()
            data: list[dict[str, Any]] = response.json()
            return data
        except httpx.HTTPError as exc:
            logger.warning(
                "order_service.get_orders_by_user failed",
                user_id=str(user_id),
                error=str(exc),
            )
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
        """Forward an admin request to the Order Service unchanged.

        The caller is responsible for setting Authorization headers via
        ``headers`` kwarg.
        """
        url = f"{self._base_url}{path}"
        response = await self._client.request(method, url, **kwargs)
        return response
