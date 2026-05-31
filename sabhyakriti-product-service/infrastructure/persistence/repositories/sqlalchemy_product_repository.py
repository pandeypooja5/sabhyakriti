"""SQLAlchemy implementation of IProductRepository."""
from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.product import Product, ProductImage
from domain.repositories.i_product_repository import IProductRepository
from domain.value_objects import SortOrder
from infrastructure.persistence.models import (
    CategoryModel,
    ProductCategoryModel,
    ProductImageModel,
    ProductModel,
)


def _model_to_entity(row: ProductModel) -> Product:
    images = [
        ProductImage(
            image_id=img.image_id,
            product_id=img.product_id,
            s3_key=img.s3_key,
            cloudfront_url=img.cloudfront_url,
            is_primary=img.is_primary,
            sort_order=img.sort_order,
            created_at=img.created_at,
        )
        for img in (row.images or [])
    ]
    return Product(
        product_id=row.product_id,
        sku=row.sku,
        name=row.name,
        slug=row.slug,
        description=row.description,
        price=row.price,
        discount_percentage=row.discount_percentage,
        stock_qty=row.stock_qty,
        is_active=row.is_active,
        average_rating=row.average_rating,
        review_count=row.review_count,
        created_at=row.created_at,
        updated_at=row.updated_at,
        images=images,
    )


# Computed discounted_price expression for SQL ordering/filtering
def _discounted_price_expr() -> sa.ColumnElement:  # type: ignore[type-arg]
    return sa.func.round(
        ProductModel.price * (1 - ProductModel.discount_percentage / 100), 2
    )


class SQLAlchemyProductRepository(IProductRepository):
    """Async SQLAlchemy product repository with dual-session support."""

    def __init__(
        self,
        write_session: AsyncSession,
        read_session: AsyncSession,
    ) -> None:
        self._write = write_session
        self._read = read_session

    # ------------------------------------------------------------------
    # Read operations (use replica session)
    # ------------------------------------------------------------------

    async def list_products(
        self,
        *,
        fabric_ids: list[UUID] | None = None,
        occasion_ids: list[UUID] | None = None,
        region_ids: list[UUID] | None = None,
        search: str | None = None,
        sort: SortOrder = SortOrder.NEWEST,
        page: int = 1,
        page_size: int = 24,
    ) -> tuple[list[Product], int]:
        stmt = (
            select(ProductModel)
            .where(ProductModel.is_active.is_(True))
        )

        # --- Filter logic: within-dimension OR, cross-dimension AND ---
        if fabric_ids:
            fabric_subq = (
                select(ProductCategoryModel.product_id)
                .join(CategoryModel, CategoryModel.category_id == ProductCategoryModel.category_id)
                .where(
                    CategoryModel.type == "FABRIC",
                    ProductCategoryModel.category_id.in_(fabric_ids),
                )
                .scalar_subquery()
            )
            stmt = stmt.where(ProductModel.product_id.in_(fabric_subq))

        if occasion_ids:
            occasion_subq = (
                select(ProductCategoryModel.product_id)
                .join(CategoryModel, CategoryModel.category_id == ProductCategoryModel.category_id)
                .where(
                    CategoryModel.type == "OCCASION",
                    ProductCategoryModel.category_id.in_(occasion_ids),
                )
                .scalar_subquery()
            )
            stmt = stmt.where(ProductModel.product_id.in_(occasion_subq))

        if region_ids:
            region_subq = (
                select(ProductCategoryModel.product_id)
                .join(CategoryModel, CategoryModel.category_id == ProductCategoryModel.category_id)
                .where(
                    CategoryModel.type == "REGION",
                    ProductCategoryModel.category_id.in_(region_ids),
                )
                .scalar_subquery()
            )
            stmt = stmt.where(ProductModel.product_id.in_(region_subq))

        # --- Full-text search ---
        if search:
            stmt = stmt.where(
                ProductModel.search_vector.op("@@")(
                    func.plainto_tsquery("english", search)
                )
            )

        # --- Count before pagination ---
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total: int = (await self._read.execute(count_stmt)).scalar_one()

        # --- Sorting ---
        if sort == SortOrder.NEWEST:
            stmt = stmt.order_by(ProductModel.created_at.desc())
        elif sort == SortOrder.PRICE_ASC:
            stmt = stmt.order_by(_discounted_price_expr().asc())
        elif sort == SortOrder.PRICE_DESC:
            stmt = stmt.order_by(_discounted_price_expr().desc())
        elif sort == SortOrder.RATING_DESC:
            stmt = stmt.order_by(ProductModel.average_rating.desc())
        elif sort == SortOrder.POPULARITY:
            stmt = stmt.order_by(ProductModel.review_count.desc())

        # --- Pagination ---
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        # Eager-load images
        from sqlalchemy.orm import selectinload
        stmt = stmt.options(selectinload(ProductModel.images))

        result = await self._read.execute(stmt)
        rows = result.scalars().all()
        return [_model_to_entity(r) for r in rows], total

    async def get_by_id(self, product_id: UUID) -> Product | None:
        from sqlalchemy.orm import selectinload
        stmt = (
            select(ProductModel)
            .where(
                ProductModel.product_id == product_id,
                ProductModel.is_active.is_(True),
            )
            .options(selectinload(ProductModel.images))
        )
        row = (await self._read.execute(stmt)).scalar_one_or_none()
        return _model_to_entity(row) if row else None

    async def get_by_slug(self, slug: str) -> Product | None:
        from sqlalchemy.orm import selectinload
        stmt = (
            select(ProductModel)
            .where(
                ProductModel.slug == slug,
                ProductModel.is_active.is_(True),
            )
            .options(selectinload(ProductModel.images))
        )
        row = (await self._read.execute(stmt)).scalar_one_or_none()
        return _model_to_entity(row) if row else None

    async def _get_by_id_write(self, product_id: UUID) -> Product | None:
        """Re-fetch a product (with images) using the write session.

        Used after stock mutations so the entity reflects the pending change
        within the active write transaction.
        """
        from sqlalchemy.orm import selectinload
        stmt = (
            select(ProductModel)
            .where(ProductModel.product_id == product_id)
            .options(selectinload(ProductModel.images))
        )
        row = (await self._write.execute(stmt)).scalar_one_or_none()
        return _model_to_entity(row) if row else None

    async def find_by_ids(self, product_ids: list[UUID]) -> list[Product]:
        from sqlalchemy import and_
        from sqlalchemy.orm import selectinload
        stmt = (
            select(ProductModel)
            .where(
                and_(
                    ProductModel.product_id.in_(product_ids),
                    ProductModel.is_active.is_(True),
                )
            )
            .options(selectinload(ProductModel.images))
        )
        rows = (await self._read.execute(stmt)).scalars().all()
        return [_model_to_entity(row) for row in rows]

    async def get_slug_set(self) -> set[str]:
        stmt = select(ProductModel.slug)
        result = await self._read.execute(stmt)
        return set(result.scalars().all())

    async def slug_exists(self, slug: str) -> bool:
        stmt = select(func.count()).where(ProductModel.slug == slug)
        count = (await self._read.execute(stmt)).scalar_one()
        return count > 0

    async def get_related_products(
        self, product_id: UUID, limit: int = 6
    ) -> list[Product]:
        from sqlalchemy.orm import selectinload
        # Products sharing at least one category
        category_ids_subq = (
            select(ProductCategoryModel.category_id)
            .where(ProductCategoryModel.product_id == product_id)
            .scalar_subquery()
        )
        related_ids_subq = (
            select(ProductCategoryModel.product_id)
            .where(
                ProductCategoryModel.category_id.in_(category_ids_subq),
                ProductCategoryModel.product_id != product_id,
            )
            .distinct()
            .scalar_subquery()
        )
        stmt = (
            select(ProductModel)
            .where(
                ProductModel.product_id.in_(related_ids_subq),
                ProductModel.is_active.is_(True),
            )
            .options(selectinload(ProductModel.images))
            .limit(limit)
        )
        result = await self._read.execute(stmt)
        return [_model_to_entity(r) for r in result.scalars().all()]

    # ------------------------------------------------------------------
    # Write operations (use primary session)
    # ------------------------------------------------------------------

    async def create(self, product: Product) -> Product:
        model = ProductModel(
            product_id=product.product_id,
            sku=product.sku,
            name=product.name,
            slug=product.slug,
            description=product.description,
            price=product.price,
            discount_percentage=product.discount_percentage,
            stock_qty=product.stock_qty,
            is_active=product.is_active,
            average_rating=product.average_rating,
            review_count=product.review_count,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )
        self._write.add(model)

        # Link categories
        for cat_id in product.category_ids:
            self._write.add(
                ProductCategoryModel(
                    product_id=product.product_id,
                    category_id=cat_id,
                )
            )

        await self._write.flush()
        # Eager-load images via explicit SELECT to avoid MissingGreenlet on refresh
        from sqlalchemy.orm import selectinload
        stmt = (
            select(ProductModel)
            .where(ProductModel.product_id == product.product_id)
            .options(selectinload(ProductModel.images))
        )
        row = (await self._write.execute(stmt)).scalar_one()
        return _model_to_entity(row)

    async def update(self, product_id: UUID, updates: dict[str, Any]) -> Product:
        from sqlalchemy.orm import selectinload

        # Handle category_ids separately
        category_ids: list[UUID] | None = updates.pop("category_ids", None)

        stmt = (
            update(ProductModel)
            .where(ProductModel.product_id == product_id)
            .values(**updates)
            .returning(ProductModel)
        )
        result = await self._write.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            raise LookupError(f"Product {product_id} not found")

        if category_ids is not None:
            # Replace category associations
            del_stmt = sa.delete(ProductCategoryModel).where(
                ProductCategoryModel.product_id == product_id
            )
            await self._write.execute(del_stmt)
            for cat_id in category_ids:
                self._write.add(
                    ProductCategoryModel(
                        product_id=product_id,
                        category_id=cat_id,
                    )
                )
            await self._write.flush()

        # Reload with relationships
        reload_stmt = (
            select(ProductModel)
            .where(ProductModel.product_id == product_id)
            .options(selectinload(ProductModel.images))
        )
        reloaded = (await self._write.execute(reload_stmt)).scalar_one()
        return _model_to_entity(reloaded)

    async def soft_delete(self, product_id: UUID) -> None:
        stmt = (
            update(ProductModel)
            .where(ProductModel.product_id == product_id)
            .values(is_active=False)
        )
        result = await self._write.execute(stmt)
        if result.rowcount == 0:
            raise LookupError(f"Product {product_id} not found")

    async def reserve_stock(self, product_id: UUID, delta: int) -> Product:
        from sqlalchemy.orm import selectinload
        stmt = (
            update(ProductModel)
            .where(
                ProductModel.product_id == product_id,
                ProductModel.stock_qty >= delta,
            )
            .values(stock_qty=ProductModel.stock_qty - delta)
            .returning(ProductModel)
        )
        result = await self._write.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            # Check if product exists at all
            exists_stmt = select(func.count()).where(
                ProductModel.product_id == product_id
            )
            count = (await self._write.execute(exists_stmt)).scalar_one()
            if count == 0:
                raise LookupError(f"Product {product_id} not found")
            raise ValueError(f"Insufficient stock to reserve {delta} units")
        # Re-fetch with images eager-loaded; the row from RETURNING has no
        # images relationship loaded, which triggers MissingGreenlet on access.
        refreshed = await self._get_by_id_write(product_id)
        return refreshed if refreshed else _model_to_entity(row)

    async def release_stock(self, product_id: UUID, delta: int) -> Product:
        stmt = (
            update(ProductModel)
            .where(ProductModel.product_id == product_id)
            .values(stock_qty=ProductModel.stock_qty + delta)
            .returning(ProductModel)
        )
        result = await self._write.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            raise LookupError(f"Product {product_id} not found")
        refreshed = await self._get_by_id_write(product_id)
        return refreshed if refreshed else _model_to_entity(row)
