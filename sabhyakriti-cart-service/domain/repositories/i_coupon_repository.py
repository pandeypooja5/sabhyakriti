"""Abstract coupon repository interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities.coupon import Coupon


class ICouponRepository(ABC):
    """Port (interface) for coupon persistence operations."""

    @abstractmethod
    async def find_by_code(self, code: str) -> Coupon | None:
        """Look up a coupon by its code (case-insensitive, normalised to upper).

        Returns None if not found.
        """
        ...

    @abstractmethod
    async def create(self, coupon: Coupon) -> Coupon:
        """Persist a new coupon and return the saved entity."""
        ...

    @abstractmethod
    async def update(self, coupon: Coupon) -> Coupon:
        """Update an existing coupon and return the updated entity."""
        ...

    @abstractmethod
    async def list_all(self) -> list[Coupon]:
        """Return all coupons (admin view)."""
        ...

    @abstractmethod
    async def deactivate(self, coupon_id: UUID) -> Coupon | None:
        """Set is_active=False on the coupon.

        Returns the updated coupon, or None if not found.
        """
        ...
