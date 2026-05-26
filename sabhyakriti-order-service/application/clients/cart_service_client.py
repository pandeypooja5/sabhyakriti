"""HTTP client for the Cart microservice."""

from __future__ import annotations

import structlog
from httpx import AsyncClient, HTTPStatusError, RequestError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from application.dtos.order_dtos import CartCheckoutDTO

logger = structlog.get_logger(__name__)


class CartServiceClient:
    """Async HTTP client wrapping the Cart Service API."""

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
    async def get_cart(self, user_id: str) -> CartCheckoutDTO:
        """Retrieve the current cart for a user."""
        async with AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            response = await client.get(
                f"/internal/v1/carts/{user_id}",
                headers=self._headers(),
            )
            response.raise_for_status()
            return CartCheckoutDTO.model_validate(response.json())

    @retry(
        retry=retry_if_exception_type(RequestError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
    )
    async def clear_cart(self, user_id: str) -> None:
        """Clear the cart after successful order placement."""
        async with AsyncClient(base_url=self._base_url, timeout=10.0) as client:
            try:
                response = await client.delete(
                    f"/internal/v1/carts/{user_id}",
                    headers=self._headers(),
                )
                response.raise_for_status()
            except HTTPStatusError as exc:
                # Log but do not propagate — order is already created
                logger.warning(
                    "cart_clear_failed",
                    user_id=user_id,
                    status_code=exc.response.status_code,
                )
