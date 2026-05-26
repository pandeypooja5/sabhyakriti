"""SQLAlchemy implementation of INotificationLogRepository."""

from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.notification_log import NotificationLog
from domain.repositories.i_notification_log_repository import INotificationLogRepository
from domain.value_objects import NotificationChannel, NotificationStatus, NotificationType
from infrastructure.persistence.models import NotificationLogModel

logger = structlog.get_logger(__name__)


class SQLAlchemyNotificationLogRepository(INotificationLogRepository):
    """Persists NotificationLog entities to PostgreSQL via async SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, log: NotificationLog) -> NotificationLog:
        """Insert a new notification_logs row and return the domain entity."""
        model = NotificationLogModel(
            id=log.id,
            notification_type=str(log.notification_type),
            channel=str(log.channel),
            recipient=log.recipient,
            status=str(log.status),
            provider=log.provider,
            error_message=log.error_message,
            created_at=log.created_at,
        )
        self._session.add(model)
        await self._session.flush()  # get DB-assigned values without full commit

        logger.debug(
            "notification_log_persisted",
            log_id=str(model.id),
            notification_type=model.notification_type,
            status=model.status,
            recipient=model.recipient,
        )

        return NotificationLog(
            id=model.id,
            notification_type=NotificationType(model.notification_type),
            channel=NotificationChannel(model.channel),
            recipient=model.recipient,
            status=NotificationStatus(model.status),
            provider=model.provider,
            error_message=model.error_message,
            created_at=model.created_at,
        )
