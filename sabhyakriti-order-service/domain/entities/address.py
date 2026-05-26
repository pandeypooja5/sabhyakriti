"""Address domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass
class Address:
    """
    A saved shipping address belonging to a user.

    Business rules:
    - Max 5 addresses per user.
    - First address created is automatically the default.
    - Deleting the current default promotes the next address.
    """

    address_id: UUID
    user_id: str
    full_name: str
    phone: str
    address_line1: str
    address_line2: str
    city: str
    state: str
    pincode: str
    is_default: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
