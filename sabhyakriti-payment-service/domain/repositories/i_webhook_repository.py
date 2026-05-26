"""Abstract webhook event repository interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.payment import WebhookEvent


class IWebhookRepository(ABC):
    """Port (interface) for idempotent webhook event persistence."""

    @abstractmethod
    async def create_if_not_exists(
        self,
        razorpay_event_id: str,
        event_type: str,
        payload: dict,  # type: ignore[type-arg]
    ) -> tuple[WebhookEvent, bool]:
        """Insert a new webhook event, or return the existing one if it already exists.

        Uses INSERT ... ON CONFLICT (razorpay_event_id) DO NOTHING to guarantee
        exactly-once processing.

        Returns:
            A ``(WebhookEvent, is_new)`` tuple where ``is_new`` is ``True`` when
            the row was freshly inserted and ``False`` for a duplicate.
        """
        ...

    @abstractmethod
    async def mark_processed(self, razorpay_event_id: str) -> None:
        """Mark a webhook event as successfully processed."""
        ...

    @abstractmethod
    async def mark_failed(
        self, razorpay_event_id: str, error: str
    ) -> None:
        """Record a processing failure on the webhook event."""
        ...
