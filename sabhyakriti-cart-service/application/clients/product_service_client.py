"""Async HTTP client for the Product Service.

Prices are always fetched live — no caching.
Fail-partial strategy: timeout returns empty dict, caller sets price_stale=True.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

import httpx
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 10.0
_BATCH_PATH = "/internal/v1/products/batch"


@dataclass(frozen=True)
class ProductPriceDTO:
    """Lightweight product info returned from Product Service batch endpoint."""

    product_id: UUID
    name: str
    slug: str
    primary_image_url: str | None
    discounted_price: Decimal
    stock_status: str  # "IN_STOCK" | "OUT_OF_STOCK" | "LIMITED"
    is_active: bool


class ProductServiceClient:
    """HTTP client for Product Service — used by Cart Application Service."""

    def __init__(self, base_url: str, internal_secret: str = "") -> None:
        self._base_url = base_url.rstrip("/")
        self._internal_secret = internal_secret

    @retry(
        retry=retry_if_exception_type(httpx.ConnectError),
        stop=stop_after_attempt(2),
        wait=wait_fixed(0.2),
        reraise=False,
    )
    async def get_products_batch(
        self,
        product_ids: list[UUID],
    ) -> dict[UUID, ProductPriceDTO]:
        """Fetch price + availability for a batch of product IDs.

        Strategy:
        - Timeout: 2 s
        - 1 retry on ConnectError (network hiccup)
        - On ReadTimeout / HTTPStatusError: return {} → caller marks price_stale=True

        Args:
            product_ids: list of product UUIDs to fetch

        Returns:
            dict keyed by product_id. Empty dict signals a partial failure.
        """
        if not product_ids:
            return {}

        payload = {"product_ids": [str(pid) for pid in product_ids]}

        try:
            headers = {}
            if self._internal_secret:
                headers["X-Internal-Secret"] = self._internal_secret
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=_TIMEOUT_SECONDS,
            ) as client:
                response = await client.post(_BATCH_PATH, json=payload, headers=headers)
                response.raise_for_status()
                data: list[dict[str, object]] = response.json()
                return {
                    UUID(str(item["product_id"])): ProductPriceDTO(
                        product_id=UUID(str(item["product_id"])),
                        name=str(item["name"]),
                        slug=str(item.get("slug", "")),
                        primary_image_url=(
                            str(item["primary_image_url"])
                            if item.get("primary_image_url")
                            else None
                        ),
                        discounted_price=Decimal(str(item["discounted_price"])),
                        stock_status=str(item["stock_status"]),
                        is_active=bool(item["is_active"]),
                    )
                    for item in data
                }
        except (httpx.TimeoutException, httpx.HTTPStatusError) as exc:
            logger.warning(
                "ProductService batch request failed — returning stale prices",
                exc_info=exc,
            )
            return {}
        except RetryError as exc:
            logger.warning(
                "ProductService batch request failed after retries",
                exc_info=exc,
            )
            return {}
