"""Abstract repository interface for NotificationLog persistence."""

from abc import ABC, abstractmethod

from domain.entities.notification_log import NotificationLog


class INotificationLogRepository(ABC):
    """Port defining persistence operations for NotificationLog entities."""

    @abstractmethod
    async def create(self, log: NotificationLog) -> NotificationLog:
        """Persist a new notification log entry and return the saved entity."""
        raise NotImplementedError
