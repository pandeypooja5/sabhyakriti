"""Category domain entity."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from domain.value_objects import CategoryType


@dataclass
class Category:
    """Domain entity for a product category / dimension."""

    category_id: UUID
    name: str
    slug: str
    type: CategoryType
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
