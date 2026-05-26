"""
Address Application Service — manages customer address book.

Business rules enforced:
- Max 5 addresses per user.
- First address is automatically set as default.
- Deleting the default address promotes the next available address.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog

from application.dtos.order_dtos import (
    AddressDTO,
    CreateAddressRequest,
    UpdateAddressRequest,
)
from domain.entities.address import Address
from domain.repositories.i_address_repository import IAddressRepository

logger = structlog.get_logger(__name__)

MAX_ADDRESSES_PER_USER = 5


def _map_to_dto(address: Address) -> AddressDTO:
    return AddressDTO(
        address_id=address.address_id,
        user_id=address.user_id,
        full_name=address.full_name,
        phone=address.phone,
        address_line1=address.address_line1,
        address_line2=address.address_line2,
        city=address.city,
        state=address.state,
        pincode=address.pincode,
        is_default=address.is_default,
        created_at=address.created_at,
        updated_at=address.updated_at,
    )


class AddressApplicationService:
    """Handles all address-book CRUD operations."""

    def __init__(self, address_repo: IAddressRepository) -> None:
        self._repo = address_repo

    async def list_addresses(self, user_id: str) -> list[AddressDTO]:
        """Return all addresses for the authenticated user."""
        addresses = await self._repo.list_by_user(user_id)
        return [_map_to_dto(a) for a in addresses]

    async def add_address(
        self,
        user_id: str,
        request: CreateAddressRequest,
    ) -> AddressDTO:
        """
        Add a new address.

        - Enforces the 5-address limit.
        - Automatically marks as default if it's the user's first address.
        """
        count = await self._repo.count_by_user(user_id)
        if count >= MAX_ADDRESSES_PER_USER:
            raise ValueError(
                f"Maximum {MAX_ADDRESSES_PER_USER} addresses allowed per user"
            )

        is_first = count == 0
        now = datetime.now(tz=timezone.utc)

        address = Address(
            address_id=uuid.uuid4(),
            user_id=user_id,
            full_name=request.full_name,
            phone=request.phone,
            address_line1=request.address_line1,
            address_line2=request.address_line2,
            city=request.city,
            state=request.state,
            pincode=request.pincode,
            is_default=is_first,
            created_at=now,
            updated_at=now,
        )

        saved = await self._repo.create(address)
        return _map_to_dto(saved)

    async def update_address(
        self,
        address_id: uuid.UUID,
        user_id: str,
        request: UpdateAddressRequest,
    ) -> AddressDTO:
        """Update a specific address (scoped to the authenticated user)."""
        existing = await self._repo.get_by_id(address_id, user_id)
        if existing is None:
            raise ValueError(f"Address {address_id} not found")

        # Apply partial updates
        updated = Address(
            address_id=existing.address_id,
            user_id=existing.user_id,
            full_name=request.full_name or existing.full_name,
            phone=request.phone or existing.phone,
            address_line1=request.address_line1 or existing.address_line1,
            address_line2=(
                request.address_line2
                if request.address_line2 is not None
                else existing.address_line2
            ),
            city=request.city or existing.city,
            state=request.state or existing.state,
            pincode=request.pincode or existing.pincode,
            is_default=existing.is_default,
            created_at=existing.created_at,
            updated_at=datetime.now(tz=timezone.utc),
        )

        saved = await self._repo.update(updated)
        return _map_to_dto(saved)

    async def delete_address(
        self,
        address_id: uuid.UUID,
        user_id: str,
    ) -> None:
        """
        Delete an address.

        If the deleted address was the default, the repository promotes the
        next available address to default.
        """
        existing = await self._repo.get_by_id(address_id, user_id)
        if existing is None:
            raise ValueError(f"Address {address_id} not found")

        await self._repo.delete(address_id, user_id)

    async def set_default(
        self,
        address_id: uuid.UUID,
        user_id: str,
    ) -> AddressDTO:
        """Set an address as the default, unsetting all others for this user."""
        existing = await self._repo.get_by_id(address_id, user_id)
        if existing is None:
            raise ValueError(f"Address {address_id} not found")

        updated = await self._repo.set_default(address_id, user_id)
        return _map_to_dto(updated)

    async def get_by_id(
        self,
        address_id: uuid.UUID,
        user_id: str,
    ) -> Address:
        """Return an Address domain entity, for use in other services."""
        address = await self._repo.get_by_id(address_id, user_id)
        if address is None:
            raise ValueError(f"Address {address_id} not found")
        return address
