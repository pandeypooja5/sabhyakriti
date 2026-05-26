"""Coupon Application Service — Flow 12: admin coupon CRUD."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from application.dtos.cart_dtos import (
    CouponDTO,
    CreateCouponRequest,
    UpdateCouponRequest,
)
from domain.entities.coupon import Coupon
from domain.repositories.i_coupon_repository import ICouponRepository
from domain.value_objects import CouponType

logger = logging.getLogger(__name__)


class CouponApplicationService:
    """Admin-facing coupon management service."""

    def __init__(self, coupon_repo: ICouponRepository) -> None:
        self._coupon_repo = coupon_repo

    async def list_coupons(self) -> list[CouponDTO]:
        """Return all coupons."""
        coupons = await self._coupon_repo.list_all()
        return [_coupon_to_dto(c) for c in coupons]

    async def create_coupon(self, request: CreateCouponRequest) -> CouponDTO:
        """Create a new coupon.

        Raises:
            ValueError: if coupon_type is invalid or code already exists
        """
        try:
            coupon_type = CouponType(request.coupon_type.upper())
        except ValueError as exc:
            raise ValueError(
                f"Invalid coupon type '{request.coupon_type}'. "
                f"Must be one of: {[t.value for t in CouponType]}"
            ) from exc

        existing = await self._coupon_repo.find_by_code(request.code)
        if existing is not None:
            raise ValueError(f"Coupon code '{request.code}' already exists.")

        now = datetime.now(tz=timezone.utc)
        coupon = Coupon(
            coupon_id=uuid4(),
            code=request.code,
            coupon_type=coupon_type,
            value=request.value,
            min_order_amount=request.min_order_amount,
            max_uses=request.max_uses,
            used_count=0,
            is_active=True,
            expires_at=request.expires_at,
            created_at=now,
            updated_at=now,
        )
        saved = await self._coupon_repo.create(coupon)
        logger.info("Created coupon %s (type=%s)", saved.code, saved.coupon_type)
        return _coupon_to_dto(saved)

    async def update_coupon(
        self,
        coupon_id: UUID,
        request: UpdateCouponRequest,
    ) -> CouponDTO:
        """Partially update a coupon.

        Raises:
            LookupError: if coupon not found
        """
        coupons = await self._coupon_repo.list_all()
        coupon = next((c for c in coupons if c.coupon_id == coupon_id), None)
        if coupon is None:
            raise LookupError(f"Coupon {coupon_id} not found.")

        updated = Coupon(
            coupon_id=coupon.coupon_id,
            code=coupon.code,
            coupon_type=coupon.coupon_type,
            value=request.value if request.value is not None else coupon.value,
            min_order_amount=request.min_order_amount
            if request.min_order_amount is not None
            else coupon.min_order_amount,
            max_uses=request.max_uses
            if request.max_uses is not None
            else coupon.max_uses,
            used_count=coupon.used_count,
            is_active=request.is_active
            if request.is_active is not None
            else coupon.is_active,
            expires_at=request.expires_at
            if request.expires_at is not None
            else coupon.expires_at,
            created_at=coupon.created_at,
            updated_at=datetime.now(tz=timezone.utc),
        )
        saved = await self._coupon_repo.update(updated)
        return _coupon_to_dto(saved)

    async def deactivate_coupon(self, coupon_id: UUID) -> CouponDTO:
        """Deactivate a coupon (soft delete).

        Raises:
            LookupError: if coupon not found
        """
        coupon = await self._coupon_repo.deactivate(coupon_id)
        if coupon is None:
            raise LookupError(f"Coupon {coupon_id} not found.")
        return _coupon_to_dto(coupon)


def _coupon_to_dto(coupon: Coupon) -> CouponDTO:
    return CouponDTO(
        coupon_id=coupon.coupon_id,
        code=coupon.code,
        type=coupon.coupon_type.value,
        value=coupon.value,
        min_order_amount=coupon.min_order_amount,
        max_uses=coupon.max_uses,
        used_count=coupon.used_count,
        is_active=coupon.is_active,
        expires_at=coupon.expires_at,
    )
