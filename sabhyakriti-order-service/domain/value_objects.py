"""Domain value objects: enumerations and immutable snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class OrderStatus(StrEnum):
    """Lifecycle states for an order."""

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    RETURN_REQUESTED = "RETURN_REQUESTED"
    RETURN_APPROVED = "RETURN_APPROVED"
    RETURN_REJECTED = "RETURN_REJECTED"
    RETURNED = "RETURNED"
    REFUNDED = "REFUNDED"


class ReturnStatus(StrEnum):
    """Lifecycle states for a return request."""

    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ITEMS_RECEIVED = "ITEMS_RECEIVED"
    REFUND_INITIATED = "REFUND_INITIATED"
    REFUNDED = "REFUNDED"


class PaymentMethod(StrEnum):
    """Supported payment methods."""

    RAZORPAY = "RAZORPAY"
    UPI = "UPI"
    COD = "COD"


@dataclass(frozen=True)
class AddressSnapshot:
    """
    Immutable snapshot of a shipping address captured at order creation.

    Stored as JSONB in the orders table so historical orders always reflect
    the address that was used, even if the user later edits or deletes it.
    """

    address_id: str
    full_name: str
    phone: str
    address_line1: str
    address_line2: str
    city: str
    state: str
    pincode: str

    def to_dict(self) -> dict[str, Any]:
        """Serialise to plain dict for JSONB storage."""
        return {
            "address_id": self.address_id,
            "full_name": self.full_name,
            "phone": self.phone,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "city": self.city,
            "state": self.state,
            "pincode": self.pincode,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AddressSnapshot":
        """Deserialise from JSONB storage."""
        return cls(
            address_id=data["address_id"],
            full_name=data["full_name"],
            phone=data["phone"],
            address_line1=data["address_line1"],
            address_line2=data["address_line2"],
            city=data["city"],
            state=data["state"],
            pincode=data["pincode"],
        )
