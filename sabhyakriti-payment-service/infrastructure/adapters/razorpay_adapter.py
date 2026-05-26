"""Razorpay SDK adapter.

The Razorpay Python SDK is synchronous, so all calls are executed in a
thread-pool executor via ``asyncio.get_event_loop().run_in_executor`` to
avoid blocking the async event loop.
"""

from __future__ import annotations

import asyncio
import functools
from typing import Any

import razorpay
import structlog

logger = structlog.get_logger(__name__)


class RazorpayAdapter:
    """Async wrapper around the synchronous Razorpay Python SDK."""

    def __init__(self, key_id: str, key_secret: str) -> None:
        self._client = razorpay.Client(auth=(key_id, key_secret))

    async def create_order(self, amount_paise: int, receipt: str) -> dict[str, Any]:
        """Create a Razorpay order and return the raw response dict.

        Args:
            amount_paise: Order amount in paise (100 paise = 1 INR).
            receipt: A unique receipt ID (typically ``order_{uuid}``).

        Returns:
            Razorpay order response dict containing at minimum ``id``,
            ``amount``, ``currency``, and ``status``.
        """
        data = {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt,
            "payment_capture": 1,
        }
        loop = asyncio.get_event_loop()
        logger.info("razorpay_create_order", amount_paise=amount_paise, receipt=receipt)
        result: dict[str, Any] = await loop.run_in_executor(
            None,
            functools.partial(self._client.order.create, data=data),
        )
        return result

    async def create_refund(
        self,
        razorpay_payment_id: str,
        amount_paise: int,
    ) -> dict[str, Any]:
        """Initiate a refund for a captured Razorpay payment.

        Args:
            razorpay_payment_id: The Razorpay payment ID (``pay_XXXX``).
            amount_paise: Refund amount in paise.

        Returns:
            Razorpay refund response dict containing ``id``, ``amount``,
            ``status``, etc.
        """
        data = {
            "amount": amount_paise,
            "speed": "normal",
        }
        loop = asyncio.get_event_loop()
        logger.info(
            "razorpay_create_refund",
            razorpay_payment_id=razorpay_payment_id,
            amount_paise=amount_paise,
        )
        result: dict[str, Any] = await loop.run_in_executor(
            None,
            functools.partial(
                self._client.payment.refund,
                razorpay_payment_id,
                data,
            ),
        )
        return result

    async def fetch_payment(self, razorpay_payment_id: str) -> dict[str, Any]:
        """Fetch payment details by Razorpay payment ID."""
        loop = asyncio.get_event_loop()
        result: dict[str, Any] = await loop.run_in_executor(
            None,
            functools.partial(self._client.payment.fetch, razorpay_payment_id),
        )
        return result
