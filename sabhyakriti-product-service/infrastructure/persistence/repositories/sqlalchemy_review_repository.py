"""SQLAlchemy implementation of IReviewRepository."""
from __future__ import annotations

from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.review import Review
from domain.repositories.i_review_repository import IReviewRepository
from infrastructure.persistence.models import ProductModel, ReviewModel


def _model_to_entity(row: ReviewModel) -> Review:
    return Review(
        review_id=row.review_id,
        product_id=row.product_id,
        user_id=row.user_id,
        rating=row.rating,
        title=row.title,
        body=row.body,
        is_verified_purchase=row.is_verified_purchase,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SQLAlchemyReviewRepository(IReviewRepository):
    """Async SQLAlchemy review repository."""

    def __init__(
        self,
        write_session: AsyncSession,
        read_session: AsyncSession,
    ) -> None:
        self._write = write_session
        self._read = read_session

    async def list_for_product(
        self, product_id: UUID, *, page: int = 1, page_size: int = 10
    ) -> tuple[list[Review], int]:
        base = select(ReviewModel).where(ReviewModel.product_id == product_id)

        count_stmt = select(func.count()).select_from(base.subquery())
        total: int = (await self._read.execute(count_stmt)).scalar_one()

        stmt = (
            base.order_by(ReviewModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._read.execute(stmt)
        return [_model_to_entity(r) for r in result.scalars().all()], total

    async def get_by_id(self, review_id: UUID) -> Review | None:
        stmt = select(ReviewModel).where(ReviewModel.review_id == review_id)
        row = (await self._read.execute(stmt)).scalar_one_or_none()
        return _model_to_entity(row) if row else None

    async def get_by_user_and_product(
        self, user_id: UUID, product_id: UUID
    ) -> Review | None:
        stmt = select(ReviewModel).where(
            ReviewModel.user_id == user_id,
            ReviewModel.product_id == product_id,
        )
        row = (await self._read.execute(stmt)).scalar_one_or_none()
        return _model_to_entity(row) if row else None

    async def create(self, review: Review) -> Review:
        model = ReviewModel(
            review_id=review.review_id,
            product_id=review.product_id,
            user_id=review.user_id,
            rating=review.rating,
            title=review.title,
            body=review.body,
            is_verified_purchase=review.is_verified_purchase,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )
        self._write.add(model)
        await self._write.flush()
        await self._write.refresh(model)
        return _model_to_entity(model)

    async def delete(self, review_id: UUID) -> None:
        stmt = sa.delete(ReviewModel).where(
            ReviewModel.review_id == review_id
        ).returning(ReviewModel.review_id)
        row = (await self._write.execute(stmt)).scalar_one_or_none()
        if row is None:
            raise LookupError(f"Review {review_id} not found")

    async def recalculate_product_stats(self, product_id: UUID) -> None:
        """Atomically update average_rating and review_count on the product."""
        stats_stmt = select(
            func.count(ReviewModel.review_id).label("cnt"),
            func.coalesce(func.avg(ReviewModel.rating), 0).label("avg_rating"),
        ).where(ReviewModel.product_id == product_id)

        stats = (await self._write.execute(stats_stmt)).one()
        review_count = int(stats.cnt)
        average_rating = round(float(stats.avg_rating), 2)

        upd_stmt = (
            update(ProductModel)
            .where(ProductModel.product_id == product_id)
            .values(review_count=review_count, average_rating=average_rating)
        )
        await self._write.execute(upd_stmt)
