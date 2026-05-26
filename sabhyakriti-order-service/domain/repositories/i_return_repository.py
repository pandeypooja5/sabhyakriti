"""Abstract interface for the ReturnRequest repository."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities.return_request import ReturnRequest
from domain.value_objects import ReturnStatus


class IReturnRepository(ABC):
    """Port (interface) for return-request persistence."""

    @abstractmethod
    async def create(self, return_request: ReturnRequest) -> ReturnRequest:
        """Persist a new return request and return it."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, return_request_id: UUID) -> ReturnRequest | None:
        """Fetch a return request by primary key."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_order_id(self, order_id: UUID) -> ReturnRequest | None:
        """Fetch the return request associated with an order."""
        raise NotImplementedError

    @abstractmethod
    async def update_status(
        self,
        return_request_id: UUID,
        new_status: ReturnStatus,
        **extra_fields: object,
    ) -> ReturnRequest:
        """Update a return request's status and any supplementary fields."""
        raise NotImplementedError

    @abstractmethod
    async def list_all(
        self,
        page: int,
        page_size: int,
        status: ReturnStatus | None = None,
    ) -> tuple[list[ReturnRequest], int]:
        """Return a paginated list of all return requests (admin use)."""
        raise NotImplementedError
