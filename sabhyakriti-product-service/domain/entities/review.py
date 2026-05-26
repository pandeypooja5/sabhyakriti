"""Review domain entity."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Review:
    """Domain entity for a product review."""

    review_id: UUID
    product_id: UUID
    user_id: UUID
    rating: int  # 1–5
    title: str
    body: str
    is_verified_purchase: bool
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not (1 <= self.rating <= 5):
            raise ValueError(f"Rating must be between 1 and 5, got {self.rating}")
