"""Domain value objects for the notification service."""

from enum import StrEnum


class NotificationChannel(StrEnum):
    """Channel through which a notification is delivered."""

    EMAIL = "EMAIL"
    SMS = "SMS"


class NotificationStatus(StrEnum):
    """Final delivery status of a notification attempt."""

    SENT = "SENT"
    FAILED = "FAILED"


class NotificationType(StrEnum):
    """Enumeration of all supported notification types."""

    # Email types
    EMAIL_VERIFICATION = "EMAIL_VERIFICATION"
    PASSWORD_RESET = "PASSWORD_RESET"
    ORDER_CONFIRMATION = "ORDER_CONFIRMATION"
    ORDER_SHIPPED = "ORDER_SHIPPED"
    ORDER_DELIVERED = "ORDER_DELIVERED"
    ORDER_CANCELLED = "ORDER_CANCELLED"
    RETURN_RECEIVED = "RETURN_RECEIVED"
    RETURN_APPROVED = "RETURN_APPROVED"
    REFUND_PROCESSED = "REFUND_PROCESSED"
    PAYMENT_RECEIPT = "PAYMENT_RECEIPT"

    # SMS types
    SMS_OTP = "SMS_OTP"
    SMS_ORDER_SHIPPED = "SMS_ORDER_SHIPPED"
    SMS_ORDER_DELIVERED = "SMS_ORDER_DELIVERED"
