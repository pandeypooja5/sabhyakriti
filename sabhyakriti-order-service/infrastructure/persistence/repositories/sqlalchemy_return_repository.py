"""SQLAlchemy async implementation of IReturnRepository."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.return_request import ReturnItem, ReturnRequest
from domain.repositories.i_return_repository import IReturnRepository
from domain.value_objects import ReturnStatus
from infrastructure.persistence.models import ReturnItemModel, ReturnRequestModel


def _model_to_item(m: ReturnItemModel) -> ReturnItem:
    return ReturnItem(
        return_item_id=m.return_item_id,
        return_request_id=m.return_request_id,
        order_item_id=m.order_item_id,
        quantity=m.quantity,
        reason=m.reason,
    )


def _model_to_entity(m: ReturnRequestModel) -> ReturnRequest:
    return ReturnRequest(
        return_request_id=m.return_request_id,
        order_id=m.order_id,
        user_id=m.user_id,
        status=ReturnStatus(m.status),
        reason=m.reason,
        items=[_model_to_item(i) for i in m.items],
        refund_amount=m.refund_amount,
        admin_notes=m.admin_notes,
        processed_by=m.processed_by,
        processed_at=m.processed_at,
        items_received_at=m.items_received_at,
        refund_initiated_at=m.refund_initiated_at,
        refunded_at=m.refunded_at,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SQLAlchemyReturnRepository(IReturnRepository):
    """Concrete SQLAlchemy implementation for return-request persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, return_request: ReturnRequest) -> ReturnRequest:
        model = ReturnRequestModel(
            return_request_id=return_request.return_request_id,
            order_id=return_request.order_id,
            user_id=return_request.user_id,
            status=return_request.status,
            reason=return_request.reason,
            refund_amount=return_request.refund_amount,
            admin_notes=return_request.admin_notes,
            processed_by=return_request.processed_by,
            processed_at=return_request.processed_at,
            items_received_at=return_request.items_received_at,
            refund_initiated_at=return_request.refund_initiated_at,
            refunded_at=return_request.refunded_at,
            created_at=return_request.created_at,
            updated_at=return_request.updated_at,
        )

        for ri in return_request.items:
            model.items.append(
                ReturnItemModel(
                    return_item_id=ri.return_item_id,
                    return_request_id=ri.return_request_id,
                    order_item_id=ri.order_item_id,
                    quantity=ri.quantity,
                    reason=ri.reason,
                )
            )

        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _model_to_entity(model)

    async def get_by_id(self, return_request_id: UUID) -> ReturnRequest | None:
        result = await self._session.execute(
            select(ReturnRequestModel).where(
                ReturnRequestModel.return_request_id == return_request_id
            )
        )
        model = result.scalars().first()
        return _model_to_entity(model) if model else None

    async def get_by_order_id(self, order_id: UUID) -> ReturnRequest | None:
        result = await self._session.execute(
            select(ReturnRequestModel).where(
                ReturnRequestModel.order_id == order_id
            )
        )
        model = result.scalars().first()
        return _model_to_entity(model) if model else None

    async def update_status(
        self,
        return_request_id: UUID,
        new_status: ReturnStatus,
        **extra_fields: object,
    ) -> ReturnRequest:
        values: dict[str, object] = {
            "status": new_status,
            "updated_at": datetime.now(tz=timezone.utc),
        }
        values.update(extra_fields)

        stmt = (
            update(ReturnRequestModel)
            .where(ReturnRequestModel.return_request_id == return_request_id)
            .values(**values)
            .returning(ReturnRequestModel)
        )
        result = await self._session.execute(stmt)
        updated_model = result.scalars().one()
        await self._session.refresh(updated_model)
        return _model_to_entity(updated_model)

    async def list_all(
        self,
        page: int,
        page_size: int,
        status: ReturnStatus | None = None,
    ) -> tuple[list[ReturnRequest], int]:
        base_q = select(ReturnRequestModel)
        if status is not None:
            base_q = base_q.where(ReturnRequestModel.status == status)

        count_result = await self._session.execute(
            select(func.count()).select_from(base_q.subquery())
        )
        total: int = count_result.scalar_one()

        offset = (page - 1) * page_size
        list_result = await self._session.execute(
            base_q.order_by(ReturnRequestModel.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        models = list_result.scalars().all()
        return [_model_to_entity(m) for m in models], total
