"""SQLAlchemy async implementation of IPaymentRepository."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.payment import Payment
from domain.repositories.i_payment_repository import IPaymentRepository
from domain.value_objects import PaymentMethod, PaymentStatus
from infrastructure.persistence.models import PaymentModel


class SQLAlchemyPaymentRepository(IPaymentRepository):
    """Async SQLAlchemy-backed payment repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    async def get_by_order_id(self, order_id: UUID) -> Payment | None:
        stmt = select(PaymentModel).where(PaymentModel.order_id == order_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_razorpay_payment_id(
        self, razorpay_payment_id: str
    ) -> Payment | None:
        stmt = select(PaymentModel).where(
            PaymentModel.razorpay_payment_id == razorpay_payment_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_stale_created(self, cutoff_dt: datetime) -> list[Payment]:
        """Return CREATED payments whose first attempt predates ``cutoff_dt``."""
        stmt = select(PaymentModel).where(
            PaymentModel.status == PaymentStatus.CREATED,
            PaymentModel.first_attempt_at < cutoff_dt,
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    async def create(self, payment: Payment) -> Payment:
        model = self._to_model(payment)
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, payment: Payment) -> Payment:
        stmt = select(PaymentModel).where(
            PaymentModel.payment_id == payment.payment_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one()

        model.status = payment.status
        model.method = payment.method
        model.razorpay_order_id = payment.razorpay_order_id
        model.razorpay_payment_id = payment.razorpay_payment_id
        model.razorpay_signature = payment.razorpay_signature
        model.attempt_count = payment.attempt_count
        model.first_attempt_at = payment.first_attempt_at
        model.captured_at = payment.captured_at
        model.refund_id = payment.refund_id
        model.refund_amount = float(payment.refund_amount) if payment.refund_amount else None
        model.refunded_at = payment.refunded_at
        model.updated_at = payment.updated_at

        await self._session.flush()
        return self._to_entity(model)

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_entity(model: PaymentModel) -> Payment:
        return Payment(
            payment_id=model.payment_id,
            order_id=model.order_id,
            user_id=model.user_id,
            amount=Decimal(str(model.amount)),
            currency=model.currency,
            method=PaymentMethod(model.method),
            status=PaymentStatus(model.status),
            razorpay_order_id=model.razorpay_order_id,
            razorpay_payment_id=model.razorpay_payment_id,
            razorpay_signature=model.razorpay_signature,
            attempt_count=model.attempt_count,
            first_attempt_at=model.first_attempt_at,
            captured_at=model.captured_at,
            refund_id=model.refund_id,
            refund_amount=Decimal(str(model.refund_amount)) if model.refund_amount else None,
            refunded_at=model.refunded_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(entity: Payment) -> PaymentModel:
        return PaymentModel(
            payment_id=entity.payment_id,
            order_id=entity.order_id,
            user_id=entity.user_id,
            amount=float(entity.amount),
            currency=entity.currency,
            method=entity.method,
            status=entity.status,
            razorpay_order_id=entity.razorpay_order_id,
            razorpay_payment_id=entity.razorpay_payment_id,
            razorpay_signature=entity.razorpay_signature,
            attempt_count=entity.attempt_count,
            first_attempt_at=entity.first_attempt_at,
            captured_at=entity.captured_at,
            refund_id=entity.refund_id,
            refund_amount=float(entity.refund_amount) if entity.refund_amount else None,
            refunded_at=entity.refunded_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
