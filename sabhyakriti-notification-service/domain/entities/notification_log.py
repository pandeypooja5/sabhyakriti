"""NotificationLog domain entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from domain.value_objects import NotificationChannel, NotificationStatus, NotificationType


@dataclass
class NotificationLog:
    """Immutable record of a single notification send attempt."""

    notification_type: NotificationType
    channel: NotificationChannel
    recipient: str  # email address or E.164 phone number
    status: NotificationStatus
    provider: str  # "SES", "TWILIO", "SNS"
    id: UUID = field(default_factory=uuid4)
    error_message: str | None = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )

    def __post_init__(self) -> None:
        if not self.recipient:
            raise ValueError("recipient must not be empty")
        if not self.provider:
            raise ValueError("provider must not be empty")
