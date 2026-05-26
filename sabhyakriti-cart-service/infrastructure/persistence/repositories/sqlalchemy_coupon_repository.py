"""SQLAlchemy implementation of ICouponRepository."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.coupon import Coupon
from domain.repositories.i_coupon_repository import ICouponRepository
from domain.value_objects import CouponType
from infrastructure.persistence.models import CouponModel

logger = logging.getLogger(__name__)


class SQLAlchamyCouponRepository(ICouponRepository):
    """Async SQLAlchemy coupon repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_code(self, code: str) -> Coupon | None:
        """Case-insensitive lookup — normalises to UPPERCASE before query."""
        normalised = code.strip().upper()
        result = await self._session.execute(
            select(CouponModel).where(CouponModel.code == normalised)
        )
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None

    async def create(self, coupon: Coupon) -> Coupon:
        model = CouponModel(
            coupon_id=coupon.coupon_id,
            code=coupon.code.upper(),
            coupon_type=coupon.coupon_type.value,
            value=coupon.value,
            min_order_amount=coupon.min_order_amount,
            max_uses=coupon.max_uses,
            used_count=coupon.used_count,
            is_active=coupon.is_active,
            expires_at=coupon.expires_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _model_to_entity(model)

    async def update(self, coupon: Coupon) -> Coupon:
        result = await self._session.execute(
            select(CouponModel).where(CouponModel.coupon_id == coupon.coupon_id)
        )
        model = result.scalar_one()
        model.value = coupon.value
        model.min_order_amount = coupon.min_order_amount
        model.max_uses = coupon.max_uses
        model.is_active = coupon.is_active
        model.expires_at = coupon.expires_at
        await self._session.flush()
        return _model_to_entity(model)

    async def list_all(self) -> list[Coupon]:
        result = await self._session.execute(
            select(CouponModel).order_by(CouponModel.created_at.desc())
        )
        return [_model_to_entity(m) for m in result.scalars().all()]

    async def deactivate(self, coupon_id: UUID) -> Coupon | None:
        result = await self._session.execute(
            select(CouponModel).where(CouponModel.coupon_id == coupon_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        model.is_active = False
        await self._session.flush()
        return _model_to_entity(model)


# ---------------------------------------------------------------------------
# Mapper helpers
# ---------------------------------------------------------------------------

def _model_to_entity(model: CouponModel) -> Coupon:
    return Coupon(
        coupon_id=model.coupon_id,
        code=model.code,
        coupon_type=CouponType(model.coupon_type),
        value=Decimal(str(model.value)),
        min_order_amount=Decimal(str(model.min_order_amount)),
        max_uses=model.max_uses,
        used_count=model.used_count,
        is_active=model.is_active,
        expires_at=model.expires_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
