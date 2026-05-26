"""SQLAlchemy async implementation of IWebhookRepository.

The ``create_if_not_exists`` method relies on PostgreSQL's
``INSERT ... ON CONFLICT DO NOTHING`` semantics to guarantee
exactly-once event delivery.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from domain.entities.payment import WebhookEvent
from domain.repositories.i_webhook_repository import IWebhookRepository
from infrastructure.persistence.models import WebhookEventModel


class SQLAlchemyWebhookRepository(IWebhookRepository):
    """Async SQLAlchemy-backed webhook event repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_if_not_exists(
        self,
        razorpay_event_id: str,
        event_type: str,
        payload: dict,  # type: ignore[type-arg]
    ) -> tuple[WebhookEvent, bool]:
        """Idempotent insert using PostgreSQL ON CONFLICT DO NOTHING.

        Returns:
            ``(WebhookEvent, True)`` when a new row was inserted.
            ``(WebhookEvent, False)`` when the event already existed.
        """
        new_id = uuid.uuid4()
        razorpay_payment_id: str | None = None
        try:
            razorpay_payment_id = (
                payload.get("payload", {})
                .get("payment", {})
                .get("entity", {})
                .get("id")
            )
        except AttributeError:
            pass

        stmt = (
            pg_insert(WebhookEventModel)
            .values(
                event_id=new_id,
                razorpay_event_id=razorpay_event_id,
                event_type=event_type,
                payload=payload,
                processed=False,
                razorpay_payment_id=razorpay_payment_id,
            )
            .on_conflict_do_nothing(index_elements=["razorpay_event_id"])
            .returning(WebhookEventModel)
        )

        result = await self._session.execute(stmt)
        inserted_model = result.scalar_one_or_none()

        if inserted_model is not None:
            # Fresh insert
            return self._to_entity(inserted_model), True

        # Conflict — fetch the existing row
        existing_stmt = select(WebhookEventModel).where(
            WebhookEventModel.razorpay_event_id == razorpay_event_id
        )
        existing_result = await self._session.execute(existing_stmt)
        existing_model = existing_result.scalar_one()
        return self._to_entity(existing_model), False

    async def mark_processed(self, razorpay_event_id: str) -> None:
        """Set processed=True and record the timestamp."""
        stmt = select(WebhookEventModel).where(
            WebhookEventModel.razorpay_event_id == razorpay_event_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.processed = True
        model.processed_at = datetime.now(tz=timezone.utc)
        model.error_message = None
        await self._session.flush()

    async def mark_failed(
        self, razorpay_event_id: str, error: str
    ) -> None:
        """Record a processing error against the webhook event."""
        stmt = select(WebhookEventModel).where(
            WebhookEventModel.razorpay_event_id == razorpay_event_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one()
        model.processed = False
        model.error_message = error
        await self._session.flush()

    # ------------------------------------------------------------------
    # Mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _to_entity(model: WebhookEventModel) -> WebhookEvent:
        return WebhookEvent(
            event_id=model.event_id,
            razorpay_event_id=model.razorpay_event_id,
            event_type=model.event_type,
            payload=model.payload,
            processed=model.processed,
            error_message=model.error_message,
            created_at=model.created_at,
            processed_at=model.processed_at,
        )
