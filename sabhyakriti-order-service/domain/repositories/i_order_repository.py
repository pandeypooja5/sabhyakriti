"""Abstract interface for the Order repository."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities.order import Order, OrderItem
from domain.value_objects import OrderStatus


class IOrderRepository(ABC):
    """Port (interface) that infrastructure adapters must implement."""

    @abstractmethod
    async def create(self, order: Order) -> Order:
        """Persist a new order and return the saved entity (with order_number)."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, order_id: UUID) -> Order | None:
        """Fetch an order by primary key using the read replica."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id_write(self, order_id: UUID) -> Order | None:
        """Fetch an order by primary key using the primary (write) engine."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_order_number(self, order_number: str) -> Order | None:
        """Fetch an order by its human-readable order number."""
        raise NotImplementedError

    @abstractmethod
    async def list_by_user(
        self,
        user_id: str,
        page: int,
        page_size: int,
        status: OrderStatus | None = None,
    ) -> tuple[list[Order], int]:
        """Return a paginated list of orders for a user and the total count."""
        raise NotImplementedError

    @abstractmethod
    async def list_all(
        self,
        page: int,
        page_size: int,
        status: OrderStatus | None = None,
    ) -> tuple[list[Order], int]:
        """Return a paginated list of all orders (admin use)."""
        raise NotImplementedError

    @abstractmethod
    async def update_status(
        self,
        order_id: UUID,
        new_status: OrderStatus,
        **timestamp_fields: object,
    ) -> Order:
        """Update an order's status and any associated timestamp fields."""
        raise NotImplementedError

    @abstractmethod
    async def get_items(self, order_id: UUID) -> list[OrderItem]:
        """Return all items belonging to an order."""
        raise NotImplementedError
