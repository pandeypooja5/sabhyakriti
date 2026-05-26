"""SQLAlchemy implementation of ICategoryRepository."""
from __future__ import annotations

from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.category import Category
from domain.repositories.i_category_repository import ICategoryRepository
from domain.value_objects import CategoryType
from infrastructure.persistence.models import (
    CategoryModel,
    ProductCategoryModel,
    ProductModel,
)


def _model_to_entity(row: CategoryModel) -> Category:
    return Category(
        category_id=row.category_id,
        name=row.name,
        slug=row.slug,
        type=CategoryType(row.type),
        display_order=row.display_order,
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SQLAlchemyCategoryRepository(ICategoryRepository):
    """Async SQLAlchemy category repository."""

    def __init__(
        self,
        write_session: AsyncSession,
        read_session: AsyncSession,
    ) -> None:
        self._write = write_session
        self._read = read_session

    async def list_categories(
        self,
        *,
        type: CategoryType | None = None,
        active_only: bool = True,
    ) -> list[Category]:
        stmt = select(CategoryModel).order_by(
            CategoryModel.display_order.asc(), CategoryModel.name.asc()
        )
        if active_only:
            stmt = stmt.where(CategoryModel.is_active.is_(True))
        if type is not None:
            stmt = stmt.where(CategoryModel.type == type.value)
        result = await self._read.execute(stmt)
        return [_model_to_entity(r) for r in result.scalars().all()]

    async def get_by_id(self, category_id: UUID) -> Category | None:
        stmt = select(CategoryModel).where(
            CategoryModel.category_id == category_id
        )
        row = (await self._read.execute(stmt)).scalar_one_or_none()
        return _model_to_entity(row) if row else None

    async def get_by_slug(self, slug: str) -> Category | None:
        stmt = select(CategoryModel).where(CategoryModel.slug == slug)
        row = (await self._read.execute(stmt)).scalar_one_or_none()
        return _model_to_entity(row) if row else None

    async def create(self, category: Category) -> Category:
        model = CategoryModel(
            category_id=category.category_id,
            name=category.name,
            slug=category.slug,
            type=category.type.value,
            display_order=category.display_order,
            is_active=category.is_active,
            created_at=category.created_at,
            updated_at=category.updated_at,
        )
        self._write.add(model)
        await self._write.flush()
        await self._write.refresh(model)
        return _model_to_entity(model)

    async def update(self, category_id: UUID, updates: dict) -> Category:  # type: ignore[type-arg]
        stmt = (
            update(CategoryModel)
            .where(CategoryModel.category_id == category_id)
            .values(**updates)
            .returning(CategoryModel)
        )
        row = (await self._write.execute(stmt)).scalar_one_or_none()
        if row is None:
            raise LookupError(f"Category {category_id} not found")
        return _model_to_entity(row)

    async def delete(self, category_id: UUID) -> None:
        stmt = sa.delete(CategoryModel).where(
            CategoryModel.category_id == category_id
        )
        result = await self._write.execute(stmt)
        if result.rowcount == 0:
            raise LookupError(f"Category {category_id} not found")

    async def has_active_products(self, category_id: UUID) -> bool:
        stmt = (
            select(func.count())
            .select_from(ProductCategoryModel)
            .join(ProductModel, ProductModel.product_id == ProductCategoryModel.product_id)
            .where(
                ProductCategoryModel.category_id == category_id,
                ProductModel.is_active.is_(True),
            )
        )
        count = (await self._read.execute(stmt)).scalar_one()
        return count > 0

    async def get_categories_for_product(self, product_id: UUID) -> list[Category]:
        stmt = (
            select(CategoryModel)
            .join(
                ProductCategoryModel,
                ProductCategoryModel.category_id == CategoryModel.category_id,
            )
            .where(ProductCategoryModel.product_id == product_id)
            .order_by(CategoryModel.type.asc(), CategoryModel.display_order.asc())
        )
        result = await self._read.execute(stmt)
        return [_model_to_entity(r) for r in result.scalars().all()]
