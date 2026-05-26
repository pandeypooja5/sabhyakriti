"""Review application service."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from uuid import UUID

import structlog

from application.clients.order_service_client import OrderServiceClient
from application.dtos.product_dtos import (
    PagedReviewsDTO,
    ReviewDTO,
    SubmitReviewRequest,
)
from domain.entities.review import Review
from domain.repositories.i_review_repository import IReviewRepository

logger = structlog.get_logger(__name__)


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class ReviewApplicationService:
    """Implements review use-cases with fail-open verified-purchase check."""

    def __init__(
        self,
        review_repo: IReviewRepository,
        order_client: OrderServiceClient,
    ) -> None:
        self._reviews = review_repo
        self._order_client = order_client

    async def list_reviews(
        self, product_id: UUID, *, page: int = 1, page_size: int = 10
    ) -> PagedReviewsDTO:
        page_size = min(page_size, 50)
        reviews, total = await self._reviews.list_for_product(
            product_id, page=page, page_size=page_size
        )
        total_pages = max(1, -(-total // page_size))
        return PagedReviewsDTO(
            items=[ReviewDTO.model_validate(r) for r in reviews],
            total_count=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def submit_review(
        self, user_id: UUID, request: SubmitReviewRequest
    ) -> ReviewDTO:
        # Check for duplicate
        existing = await self._reviews.get_by_user_and_product(
            user_id, request.product_id
        )
        if existing is not None:
            raise ValueError("You have already submitted a review for this product")

        # Fail-open verified purchase check
        verified: bool | None = await self._order_client.is_verified_purchase(
            user_id, request.product_id
        )
        is_verified = bool(verified)  # None → False (fail-open: allow review, mark unverified)

        if verified is None:
            logger.warning(
                "order_service_unreachable_during_review",
                user_id=str(user_id),
                product_id=str(request.product_id),
            )

        now = _utcnow()
        review = Review(
            review_id=uuid.uuid4(),
            product_id=request.product_id,
            user_id=user_id,
            rating=request.rating,
            title=request.title,
            body=request.body,
            is_verified_purchase=is_verified,
            created_at=now,
            updated_at=now,
        )
        saved = await self._reviews.create(review)
        await self._reviews.recalculate_product_stats(request.product_id)
        return ReviewDTO.model_validate(saved)

    async def delete_review(
        self, review_id: UUID, *, requesting_user_id: UUID, is_admin: bool
    ) -> None:
        review = await self._reviews.get_by_id(review_id)
        if review is None:
            raise LookupError(f"Review {review_id} not found")

        if not is_admin and review.user_id != requesting_user_id:
            raise PermissionError("You can only delete your own reviews")

        product_id = review.product_id
        await self._reviews.delete(review_id)
        await self._reviews.recalculate_product_stats(product_id)
