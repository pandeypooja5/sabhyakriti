"""SQLAlchemy implementation of IWishlistRepository."""

from __future__ import annotations

import logging
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.wishlist import Wishlist, WishlistItem
from domain.repositories.i_wishlist_repository import IWishlistRepository
from infrastructure.persistence.models import WishlistItemModel, WishlistModel

logger = logging.getLogger(__name__)


class SQLAlchemyWishlistRepository(IWishlistRepository):
    """Async SQLAlchemy wishlist repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: UUID) -> Wishlist | None:
        result = await self._session.execute(
            select(WishlistModel).where(WishlistModel.user_id == user_id)
        )
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None

    async def get_or_create(self, user_id: UUID) -> Wishlist:
        result = await self._session.execute(
            select(WishlistModel)
            .where(WishlistModel.user_id == user_id)
            .with_for_update()
        )
        model = result.scalar_one_or_none()

        if model is None:
            model = WishlistModel(wishlist_id=uuid4(), user_id=user_id)
            self._session.add(model)
            await self._session.flush()
            logger.info("Created new wishlist for user %s", user_id)

        return _model_to_entity(model)

    async def get_items(self, wishlist_id: UUID) -> list[WishlistItem]:
        result = await self._session.execute(
            select(WishlistItemModel)
            .where(WishlistItemModel.wishlist_id == wishlist_id)
            .order_by(WishlistItemModel.added_at)
        )
        return [_item_model_to_entity(m) for m in result.scalars().all()]

    async def add_item(
        self,
        wishlist_id: UUID,
        product_id: UUID,
    ) -> WishlistItem:
        """Idempotent add — returns existing item if already present."""
        existing_result = await self._session.execute(
            select(WishlistItemModel).where(
                WishlistItemModel.wishlist_id == wishlist_id,
                WishlistItemModel.product_id == product_id,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing is not None:
            return _item_model_to_entity(existing)

        new_item = WishlistItemModel(
            wishlist_item_id=uuid4(),
            wishlist_id=wishlist_id,
            product_id=product_id,
        )
        self._session.add(new_item)
        await self._session.flush()
        await self._session.refresh(new_item)
        return _item_model_to_entity(new_item)

    async def remove_item(
        self,
        wishlist_id: UUID,
        product_id: UUID,
    ) -> bool:
        result = await self._session.execute(
            delete(WishlistItemModel).where(
                WishlistItemModel.wishlist_id == wishlist_id,
                WishlistItemModel.product_id == product_id,
            )
        )
        return result.rowcount > 0


# ---------------------------------------------------------------------------
# Mapper helpers
# ---------------------------------------------------------------------------

def _model_to_entity(model: WishlistModel) -> Wishlist:
    return Wishlist(
        wishlist_id=model.wishlist_id,
        user_id=model.user_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _item_model_to_entity(model: WishlistItemModel) -> WishlistItem:
    return WishlistItem(
        wishlist_item_id=model.wishlist_item_id,
        wishlist_id=model.wishlist_id,
        product_id=model.product_id,
        added_at=model.added_at,
    )
