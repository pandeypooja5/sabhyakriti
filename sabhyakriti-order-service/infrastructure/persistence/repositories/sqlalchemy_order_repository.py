"""
SQLAlchemy async implementation of IOrderRepository.

- Writes go to the primary engine session.
- Reads go to the replica engine session.
- Order numbers are generated via PostgreSQL sequence `order.order_seq`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.order import Order, OrderItem
from domain.repositories.i_order_repository import IOrderRepository
from domain.value_objects import AddressSnapshot, OrderStatus, PaymentMethod
from infrastructure.persistence.models import OrderItemModel, OrderModel

_SCHEMA = "order"


def _model_to_item(m: OrderItemModel) -> OrderItem:
    return OrderItem(
        order_item_id=m.order_item_id,
        order_id=m.order_id,
        product_id=m.product_id,
        variant_id=m.variant_id,
        product_name=m.product_name,
        product_image_url=m.product_image_url,
        unit_price=m.unit_price,
        discounted_price=m.discounted_price,
        quantity=m.quantity,
        hsn_code=m.hsn_code,
        cgst_rate=m.cgst_rate,
        sgst_rate=m.sgst_rate,
        created_at=m.created_at,
    )


def _model_to_entity(m: OrderModel) -> Order:
    return Order(
        order_id=m.order_id,
        user_id=m.user_id,
        order_number=m.order_number,
        status=OrderStatus(m.status),
        payment_method=PaymentMethod(m.payment_method),
        payment_reference=m.payment_reference,
        shipping_address=AddressSnapshot.from_dict(m.shipping_address),
        subtotal=m.subtotal,
        discount_amount=m.discount_amount,
        shipping_charge=m.shipping_charge,
        cgst_amount=m.cgst_amount,
        sgst_amount=m.sgst_amount,
        total_amount=m.total_amount,
        notes=m.notes,
        cancellation_reason=m.cancellation_reason,
        confirmed_at=m.confirmed_at,
        shipped_at=m.shipped_at,
        delivered_at=m.delivered_at,
        cancelled_at=m.cancelled_at,
        created_at=m.created_at,
        updated_at=m.updated_at,
        items=[_model_to_item(i) for i in m.items],
    )


class SQLAlchemyOrderRepository(IOrderRepository):
    """Concrete SQLAlchemy implementation."""

    def __init__(
        self,
        write_session: AsyncSession,
        read_session: AsyncSession,
    ) -> None:
        self._write = write_session
        self._read = read_session

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _next_order_number(self) -> str:
        """
        Generate next order number using PostgreSQL sequence.

        Format: SKB-{YYYYMM}-{SEQ:06d}
        """
        result = await self._write.execute(
            text(f'SELECT nextval(\'"{_SCHEMA}".order_seq\')')
        )
        seq_val: int = result.scalar_one()
        now = datetime.now(tz=timezone.utc)
        return f"SKB-{now.strftime('%Y%m')}-{seq_val:06d}"

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def create(self, order: Order) -> Order:
        order_number = await self._next_order_number()

        order_model = OrderModel(
            order_id=order.order_id,
            user_id=order.user_id,
            order_number=order_number,
            status=order.status,
            payment_method=order.payment_method,
            payment_reference=order.payment_reference,
            shipping_address=order.shipping_address.to_dict(),
            subtotal=order.subtotal,
            discount_amount=order.discount_amount,
            shipping_charge=order.shipping_charge,
            cgst_amount=order.cgst_amount,
            sgst_amount=order.sgst_amount,
            total_amount=order.total_amount,
            notes=order.notes,
            confirmed_at=order.confirmed_at,
            shipped_at=order.shipped_at,
            delivered_at=order.delivered_at,
            cancelled_at=order.cancelled_at,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

        for item in order.items:
            order_model.items.append(
                OrderItemModel(
                    order_item_id=item.order_item_id,
                    order_id=item.order_id,
                    product_id=item.product_id,
                    variant_id=item.variant_id,
                    product_name=item.product_name,
                    product_image_url=item.product_image_url,
                    unit_price=item.unit_price,
                    discounted_price=item.discounted_price,
                    quantity=item.quantity,
                    hsn_code=item.hsn_code,
                    cgst_rate=item.cgst_rate,
                    sgst_rate=item.sgst_rate,
                    created_at=item.created_at,
                )
            )

        self._write.add(order_model)
        await self._write.flush()
        await self._write.refresh(order_model)
        result = _model_to_entity(order_model)
        # patch in the generated order number
        object.__setattr__(result, "order_number", order_number) if hasattr(
            result, "__setattr__"
        ) else None
        result.order_number = order_number
        return result

    async def update_status(
        self,
        order_id: UUID,
        new_status: OrderStatus,
        **timestamp_fields: object,
    ) -> Order:
        values: dict[str, object] = {
            "status": new_status,
            "updated_at": datetime.now(tz=timezone.utc),
        }
        values.update(timestamp_fields)

        stmt = (
            update(OrderModel)
            .where(OrderModel.order_id == order_id)
            .values(**values)
            .returning(OrderModel)
        )
        result = await self._write.execute(stmt)
        updated_model = result.scalars().one()
        # Refresh to load relationships
        await self._write.refresh(updated_model)
        return _model_to_entity(updated_model)

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def get_by_id(self, order_id: UUID) -> Order | None:
        result = await self._read.execute(
            select(OrderModel).where(OrderModel.order_id == order_id)
        )
        model = result.scalars().first()
        return _model_to_entity(model) if model else None

    async def get_by_id_write(self, order_id: UUID) -> Order | None:
        result = await self._write.execute(
            select(OrderModel).where(OrderModel.order_id == order_id)
        )
        model = result.scalars().first()
        return _model_to_entity(model) if model else None

    async def get_by_order_number(self, order_number: str) -> Order | None:
        result = await self._read.execute(
            select(OrderModel).where(OrderModel.order_number == order_number)
        )
        model = result.scalars().first()
        return _model_to_entity(model) if model else None

    async def list_by_user(
        self,
        user_id: str,
        page: int,
        page_size: int,
        status: OrderStatus | None = None,
    ) -> tuple[list[Order], int]:
        base_q = select(OrderModel).where(OrderModel.user_id == user_id)
        if status is not None:
            base_q = base_q.where(OrderModel.status == status)

        count_result = await self._read.execute(
            select(func.count()).select_from(base_q.subquery())
        )
        total: int = count_result.scalar_one()

        offset = (page - 1) * page_size
        list_result = await self._read.execute(
            base_q.order_by(OrderModel.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        models = list_result.scalars().all()
        return [_model_to_entity(m) for m in models], total

    async def list_all(
        self,
        page: int,
        page_size: int,
        status: OrderStatus | None = None,
    ) -> tuple[list[Order], int]:
        base_q = select(OrderModel)
        if status is not None:
            base_q = base_q.where(OrderModel.status == status)

        count_result = await self._read.execute(
            select(func.count()).select_from(base_q.subquery())
        )
        total: int = count_result.scalar_one()

        offset = (page - 1) * page_size
        list_result = await self._read.execute(
            base_q.order_by(OrderModel.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        models = list_result.scalars().all()
        return [_model_to_entity(m) for m in models], total

    async def get_items(self, order_id: UUID) -> list[OrderItem]:
        result = await self._read.execute(
            select(OrderItemModel).where(OrderItemModel.order_id == order_id)
        )
        models = result.scalars().all()
        return [_model_to_item(m) for m in models]
