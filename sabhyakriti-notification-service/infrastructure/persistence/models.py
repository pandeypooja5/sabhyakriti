"""SQLAlchemy ORM model for the notification.notification_logs table."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from domain.value_objects import NotificationChannel, NotificationStatus, NotificationType


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models in this service."""


class NotificationLogModel(Base):
    """Persistence model for a single notification send attempt."""

    __tablename__ = "notification_logs"
    __table_args__ = {"schema": "notification"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    notification_type: Mapped[str] = mapped_column(
        Enum(NotificationType, schema="notification", name="notification_type_enum"),
        nullable=False,
        index=True,
    )
    channel: Mapped[str] = mapped_column(
        Enum(NotificationChannel, schema="notification", name="notification_channel_enum"),
        nullable=False,
        index=True,
    )
    recipient: Mapped[str] = mapped_column(
        String(320),  # max email length per RFC 5321
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        Enum(NotificationStatus, schema="notification", name="notification_status_enum"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(tz=timezone.utc),
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<NotificationLogModel id={self.id} type={self.notification_type} "
            f"status={self.status} recipient={self.recipient!r}>"
        )
