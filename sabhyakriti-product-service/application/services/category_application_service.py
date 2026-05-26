"""Category application service."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from uuid import UUID

from application.dtos.product_dtos import (
    CategoryDTO,
    CreateCategoryRequest,
    UpdateCategoryRequest,
)
from domain.entities.category import Category
from domain.repositories.i_category_repository import ICategoryRepository
from domain.services.slug_service import generate_slug, make_unique_slug
from domain.value_objects import CategoryType


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class CategoryApplicationService:
    """Implements category management use-cases."""

    def __init__(self, category_repo: ICategoryRepository) -> None:
        self._categories = category_repo

    async def list_categories(
        self, *, type: CategoryType | None = None
    ) -> list[CategoryDTO]:
        cats = await self._categories.list_categories(type=type)
        return [CategoryDTO.model_validate(c) for c in cats]

    async def get_category(self, category_id: UUID) -> CategoryDTO:
        cat = await self._categories.get_by_id(category_id)
        if cat is None:
            raise LookupError(f"Category {category_id} not found")
        return CategoryDTO.model_validate(cat)

    async def create_category(self, request: CreateCategoryRequest) -> CategoryDTO:
        base_slug = generate_slug(request.name)
        # Build existing set
        all_cats = await self._categories.list_categories(active_only=False)
        existing_slugs = {c.slug for c in all_cats}
        slug = make_unique_slug(base_slug, existing_slugs)

        now = _utcnow()
        category = Category(
            category_id=uuid.uuid4(),
            name=request.name,
            slug=slug,
            type=request.type,
            display_order=request.display_order,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        saved = await self._categories.create(category)
        return CategoryDTO.model_validate(saved)

    async def update_category(
        self, category_id: UUID, request: UpdateCategoryRequest
    ) -> CategoryDTO:
        updates: dict = {}  # type: ignore[type-arg]
        if request.name is not None:
            updates["name"] = request.name
        if request.display_order is not None:
            updates["display_order"] = request.display_order
        if request.is_active is not None:
            updates["is_active"] = request.is_active
        updates["updated_at"] = _utcnow()

        updated = await self._categories.update(category_id, updates)
        return CategoryDTO.model_validate(updated)

    async def delete_category(self, category_id: UUID) -> None:
        has_products = await self._categories.has_active_products(category_id)
        if has_products:
            raise ValueError(
                "Cannot delete a category that has active products assigned to it"
            )
        await self._categories.delete(category_id)
