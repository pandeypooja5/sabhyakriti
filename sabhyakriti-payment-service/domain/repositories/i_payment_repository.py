"""Abstract payment repository interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from domain.entities.payment import Payment


class IPaymentRepository(ABC):
    """Port (interface) that all payment repository adapters must implement."""

    @abstractmethod
    async def get_by_order_id(self, order_id: UUID) -> Payment | None:
        """Fetch a payment by its associated order ID."""
        ...

    @abstractmethod
    async def get_by_razorpay_payment_id(
        self, razorpay_payment_id: str
    ) -> Payment | None:
        """Fetch a payment by its Razorpay payment ID (``pay_XXXX``)."""
        ...

    @abstractmethod
    async def create(self, payment: Payment) -> Payment:
        """Persist a new payment and return the saved entity."""
        ...

    @abstractmethod
    async def update(self, payment: Payment) -> Payment:
        """Persist changes to an existing payment and return the updated entity."""
        ...

    @abstractmethod
    async def list_stale_created(self, cutoff_dt: datetime) -> list[Payment]:
        """Return all payments in CREATED status whose first attempt predates ``cutoff_dt``.

        Used by the auto-cancel background job to cancel timed-out payments.
        """
        ...
