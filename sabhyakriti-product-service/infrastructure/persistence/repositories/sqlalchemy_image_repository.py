"""SQLAlchemy implementation of IImageRepository."""
from __future__ import annotations

from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.product import ProductImage
from domain.repositories.i_image_repository import IImageRepository
from infrastructure.persistence.models import ProductImageModel


def _model_to_entity(row: ProductImageModel) -> ProductImage:
    return ProductImage(
        image_id=row.image_id,
        product_id=row.product_id,
        s3_key=row.s3_key,
        cloudfront_url=row.cloudfront_url,
        is_primary=row.is_primary,
        sort_order=row.sort_order,
        created_at=row.created_at,
    )


class SQLAlchemyImageRepository(IImageRepository):
    """Async SQLAlchemy image repository."""

    def __init__(
        self,
        write_session: AsyncSession,
        read_session: AsyncSession,
    ) -> None:
        self._write = write_session
        self._read = read_session

    async def list_for_product(self, product_id: UUID) -> list[ProductImage]:
        stmt = (
            select(ProductImageModel)
            .where(ProductImageModel.product_id == product_id)
            .order_by(ProductImageModel.sort_order.asc(), ProductImageModel.created_at.asc())
        )
        result = await self._read.execute(stmt)
        return [_model_to_entity(r) for r in result.scalars().all()]

    async def get_by_id(self, image_id: UUID) -> ProductImage | None:
        stmt = select(ProductImageModel).where(ProductImageModel.image_id == image_id)
        row = (await self._read.execute(stmt)).scalar_one_or_none()
        return _model_to_entity(row) if row else None

    async def count_for_product(self, product_id: UUID) -> int:
        stmt = select(func.count()).where(
            ProductImageModel.product_id == product_id
        )
        return (await self._read.execute(stmt)).scalar_one()

    async def create(self, image: ProductImage) -> ProductImage:
        model = ProductImageModel(
            image_id=image.image_id,
            product_id=image.product_id,
            s3_key=image.s3_key,
            cloudfront_url=image.cloudfront_url,
            is_primary=image.is_primary,
            sort_order=image.sort_order,
            created_at=image.created_at,
        )
        self._write.add(model)
        await self._write.flush()
        await self._write.refresh(model)
        return _model_to_entity(model)

    async def clear_primary_flag(self, product_id: UUID) -> None:
        stmt = (
            update(ProductImageModel)
            .where(ProductImageModel.product_id == product_id)
            .values(is_primary=False)
        )
        await self._write.execute(stmt)

    async def set_primary(self, image_id: UUID) -> None:
        stmt = (
            update(ProductImageModel)
            .where(ProductImageModel.image_id == image_id)
            .values(is_primary=True)
            .returning(ProductImageModel.image_id)
        )
        row = (await self._write.execute(stmt)).scalar_one_or_none()
        if row is None:
            raise LookupError(f"Image {image_id} not found")

    async def delete(self, image_id: UUID) -> None:
        stmt = sa.delete(ProductImageModel).where(
            ProductImageModel.image_id == image_id
        ).returning(ProductImageModel.image_id)
        row = (await self._write.execute(stmt)).scalar_one_or_none()
        if row is None:
            raise LookupError(f"Image {image_id} not found")

    async def promote_first_as_primary(self, product_id: UUID) -> None:
        """Set the lowest sort_order image as primary if any images remain."""
        stmt = (
            select(ProductImageModel.image_id)
            .where(ProductImageModel.product_id == product_id)
            .order_by(
                ProductImageModel.sort_order.asc(),
                ProductImageModel.created_at.asc(),
            )
            .limit(1)
        )
        image_id = (await self._write.execute(stmt)).scalar_one_or_none()
        if image_id is not None:
            await self.set_primary(image_id)
