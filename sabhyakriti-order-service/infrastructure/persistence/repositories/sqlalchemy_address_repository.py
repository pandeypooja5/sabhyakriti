"""SQLAlchemy async implementation of IAddressRepository."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.address import Address
from domain.repositories.i_address_repository import IAddressRepository
from infrastructure.persistence.models import AddressModel


def _model_to_entity(m: AddressModel) -> Address:
    return Address(
        address_id=m.address_id,
        user_id=m.user_id,
        full_name=m.full_name,
        phone=m.phone,
        address_line1=m.address_line1,
        address_line2=m.address_line2,
        city=m.city,
        state=m.state,
        pincode=m.pincode,
        is_default=m.is_default,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SQLAlchemyAddressRepository(IAddressRepository):
    """Concrete SQLAlchemy implementation for address persistence."""

    def __init__(self, session: AsyncSession) -> None:
        # Address operations always use the write session for simplicity
        # (address lists are small and don't warrant replica routing)
        self._session = session

    async def list_by_user(self, user_id: str) -> list[Address]:
        result = await self._session.execute(
            select(AddressModel)
            .where(AddressModel.user_id == user_id)
            .order_by(AddressModel.is_default.desc(), AddressModel.created_at.asc())
        )
        return [_model_to_entity(m) for m in result.scalars().all()]

    async def get_by_id(self, address_id: UUID, user_id: str) -> Address | None:
        result = await self._session.execute(
            select(AddressModel).where(
                AddressModel.address_id == address_id,
                AddressModel.user_id == user_id,
            )
        )
        model = result.scalars().first()
        return _model_to_entity(model) if model else None

    async def create(self, address: Address) -> Address:
        model = AddressModel(
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
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _model_to_entity(model)

    async def update(self, address: Address) -> Address:
        stmt = (
            update(AddressModel)
            .where(AddressModel.address_id == address.address_id)
            .values(
                full_name=address.full_name,
                phone=address.phone,
                address_line1=address.address_line1,
                address_line2=address.address_line2,
                city=address.city,
                state=address.state,
                pincode=address.pincode,
                updated_at=datetime.now(tz=timezone.utc),
            )
            .returning(AddressModel)
        )
        result = await self._session.execute(stmt)
        return _model_to_entity(result.scalars().one())

    async def delete(self, address_id: UUID, user_id: str) -> None:
        # Check if it's the default before deleting
        target = await self._session.get(AddressModel, address_id)
        if target is None:
            return

        was_default = target.is_default
        await self._session.delete(target)
        await self._session.flush()

        # Promote the next address to default if needed
        if was_default:
            result = await self._session.execute(
                select(AddressModel)
                .where(AddressModel.user_id == user_id)
                .order_by(AddressModel.created_at.asc())
                .limit(1)
            )
            next_addr = result.scalars().first()
            if next_addr:
                await self._session.execute(
                    update(AddressModel)
                    .where(AddressModel.address_id == next_addr.address_id)
                    .values(is_default=True)
                )

    async def set_default(self, address_id: UUID, user_id: str) -> Address:
        # Unset all defaults for this user
        await self._session.execute(
            update(AddressModel)
            .where(AddressModel.user_id == user_id)
            .values(is_default=False)
        )
        # Set the requested one
        stmt = (
            update(AddressModel)
            .where(AddressModel.address_id == address_id)
            .values(is_default=True)
            .returning(AddressModel)
        )
        result = await self._session.execute(stmt)
        return _model_to_entity(result.scalars().one())

    async def count_by_user(self, user_id: str) -> int:
        result = await self._session.execute(
            select(func.count()).where(AddressModel.user_id == user_id)
        )
        return result.scalar_one()
