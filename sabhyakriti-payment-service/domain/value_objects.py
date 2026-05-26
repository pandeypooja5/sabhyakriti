"""Domain value objects for the payment service."""

from enum import StrEnum


class PaymentStatus(StrEnum):
    """Lifecycle states of a payment."""

    CREATED = "CREATED"
    CAPTURED = "CAPTURED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class PaymentMethod(StrEnum):
    """Supported payment methods."""

    RAZORPAY = "RAZORPAY"
    UPI = "UPI"
    COD = "COD"
