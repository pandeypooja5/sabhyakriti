"""SQLAlchemy implementation of ICartRepository."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import delete, func, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.cart import Cart, CartItem
from domain.repositories.i_cart_repository import ICartRepository
from infrastructure.persistence.models import CartItemModel, CartModel

logger = logging.getLogger(__name__)

_MAX_ITEMS = 20
_MAX_QTY = 10


class SQLAlchemyCartRepository(ICartRepository):
    """Async SQLAlchemy cart repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: UUID) -> Cart | None:
        result = await self._session.execute(
            select(CartModel).where(CartModel.user_id == user_id)
        )
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None

    async def get_or_create(self, user_id: UUID) -> Cart:
        """SELECT FOR UPDATE prevents duplicate cart creation under concurrency."""
        result = await self._session.execute(
            select(CartModel)
            .where(CartModel.user_id == user_id)
            .with_for_update()
        )
        model = result.scalar_one_or_none()

        if model is None:
            model = CartModel(cart_id=uuid4(), user_id=user_id)
            self._session.add(model)
            await self._session.flush()
            logger.info("Created new cart for user %s", user_id)

        return _model_to_entity(model)

    async def get_items(self, cart_id: UUID) -> list[CartItem]:
        result = await self._session.execute(
            select(CartItemModel)
            .where(CartItemModel.cart_id == cart_id)
            .order_by(CartItemModel.added_at)
        )
        return [_item_model_to_entity(m) for m in result.scalars().all()]

    async def add_item(
        self,
        cart_id: UUID,
        product_id: UUID,
        quantity: int,
    ) -> CartItem:
        """Upsert cart item using PostgreSQL INSERT ... ON CONFLICT DO UPDATE.

        Enforces:
        - Max 20 distinct products per cart
        - Max quantity 10 per item

        Raises:
            ValueError: if either constraint would be violated
        """
        # Check if product already in cart
        existing_result = await self._session.execute(
            select(CartItemModel).where(
                CartItemModel.cart_id == cart_id,
                CartItemModel.product_id == product_id,
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing is None:
            # Check max distinct items constraint
            count = await self.get_item_count(cart_id)
            if count >= _MAX_ITEMS:
                raise ValueError(
                    f"Cart cannot have more than {_MAX_ITEMS} distinct products."
                )
            if quantity > _MAX_QTY:
                raise ValueError(f"Quantity cannot exceed {_MAX_QTY} per item.")

            new_item = CartItemModel(
                cart_item_id=uuid4(),
                cart_id=cart_id,
                product_id=product_id,
                quantity=quantity,
            )
            self._session.add(new_item)
            await self._session.flush()
            await self._session.refresh(new_item)
            return _item_model_to_entity(new_item)
        else:
            # Increment quantity (upsert path)
            new_qty = existing.quantity + quantity
            if new_qty > _MAX_QTY:
                raise ValueError(
                    f"Adding {quantity} would exceed maximum quantity of {_MAX_QTY}. "
                    f"Current: {existing.quantity}."
                )
            await self._session.execute(
                update(CartItemModel)
                .where(CartItemModel.cart_item_id == existing.cart_item_id)
                .values(quantity=new_qty)
            )
            await self._session.flush()
            await self._session.refresh(existing)
            return _item_model_to_entity(existing)

    async def update_item_quantity(
        self,
        cart_item_id: UUID,
        cart_id: UUID,
        quantity: int,
    ) -> CartItem | None:
        if quantity > _MAX_QTY:
            raise ValueError(f"Quantity cannot exceed {_MAX_QTY} per item.")

        result = await self._session.execute(
            select(CartItemModel).where(
                CartItemModel.cart_item_id == cart_item_id,
                CartItemModel.cart_id == cart_id,
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None

        model.quantity = quantity
        await self._session.flush()
        return _item_model_to_entity(model)

    async def remove_item(self, cart_item_id: UUID, cart_id: UUID) -> bool:
        result = await self._session.execute(
            delete(CartItemModel).where(
                CartItemModel.cart_item_id == cart_item_id,
                CartItemModel.cart_id == cart_id,
            )
        )
        return result.rowcount > 0

    async def apply_coupon(self, cart_id: UUID, coupon_code: str) -> Cart:
        result = await self._session.execute(
            select(CartModel).where(CartModel.cart_id == cart_id)
        )
        model = result.scalar_one()
        model.applied_coupon_code = coupon_code.upper()
        await self._session.flush()
        return _model_to_entity(model)

    async def remove_coupon(self, cart_id: UUID) -> Cart:
        result = await self._session.execute(
            select(CartModel).where(CartModel.cart_id == cart_id)
        )
        model = result.scalar_one()
        model.applied_coupon_code = None
        await self._session.flush()
        return _model_to_entity(model)

    async def clear_cart(self, cart_id: UUID) -> None:
        """Delete all items and clear coupon — idempotent."""
        await self._session.execute(
            delete(CartItemModel).where(CartItemModel.cart_id == cart_id)
        )
        await self._session.execute(
            update(CartModel)
            .where(CartModel.cart_id == cart_id)
            .values(applied_coupon_code=None)
        )
        await self._session.flush()

    async def get_item_count(self, cart_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count(CartItemModel.product_id.distinct())).where(
                CartItemModel.cart_id == cart_id
            )
        )
        return result.scalar_one() or 0


# ---------------------------------------------------------------------------
# Mapper helpers
# ---------------------------------------------------------------------------

def _model_to_entity(model: CartModel) -> Cart:
    return Cart(
        cart_id=model.cart_id,
        user_id=model.user_id,
        applied_coupon_code=model.applied_coupon_code,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _item_model_to_entity(model: CartItemModel) -> CartItem:
    return CartItem(
        cart_item_id=model.cart_item_id,
        cart_id=model.cart_id,
        product_id=model.product_id,
        quantity=model.quantity,
        added_at=model.added_at,
    )
