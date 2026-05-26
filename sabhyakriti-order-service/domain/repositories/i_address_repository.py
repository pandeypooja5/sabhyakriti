"""Abstract interface for the Address repository."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities.address import Address


class IAddressRepository(ABC):
    """Port (interface) for address persistence."""

    @abstractmethod
    async def list_by_user(self, user_id: str) -> list[Address]:
        """Return all addresses for a user."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, address_id: UUID, user_id: str) -> Address | None:
        """Return a specific address, scoped to user for IDOR prevention."""
        raise NotImplementedError

    @abstractmethod
    async def create(self, address: Address) -> Address:
        """Persist a new address and return it."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, address: Address) -> Address:
        """Update an existing address and return it."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, address_id: UUID, user_id: str) -> None:
        """Delete an address; promote next address to default if needed."""
        raise NotImplementedError

    @abstractmethod
    async def set_default(self, address_id: UUID, user_id: str) -> Address:
        """
        Mark address as default and unset default on all others for this user.
        """
        raise NotImplementedError

    @abstractmethod
    async def count_by_user(self, user_id: str) -> int:
        """Return total address count for a user."""
        raise NotImplementedError
