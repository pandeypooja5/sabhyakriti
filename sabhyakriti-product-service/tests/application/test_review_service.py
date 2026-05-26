"""Tests for ReviewApplicationService."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from application.clients.order_service_client import OrderServiceClient
from application.dtos.product_dtos import SubmitReviewRequest
from application.services.review_application_service import ReviewApplicationService
from domain.entities.review import Review
from tests.conftest import make_review


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


@pytest.fixture
def review_svc(mock_review_repo, mock_order_client):
    return ReviewApplicationService(
        review_repo=mock_review_repo,
        order_client=mock_order_client,
    )


# ---------------------------------------------------------------------------
# submit_review tests
# ---------------------------------------------------------------------------


async def test_submit_review_verified_purchase_true(
    review_svc, mock_review_repo, mock_order_client
):
    """Review submitted with is_verified_purchase=True when order service returns True."""
    user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    mock_order_client.is_verified_purchase.return_value = True
    mock_review_repo.get_by_user_and_product.return_value = None

    saved_review = make_review(
        product_id=product_id,
        user_id=user_id,
        is_verified_purchase=True,
    )
    mock_review_repo.create.return_value = saved_review

    request = SubmitReviewRequest(
        product_id=product_id,
        rating=5,
        title="Excellent!",
        body="Beautiful saree, great quality.",
    )
    result = await review_svc.submit_review(user_id, request)

    assert result.is_verified_purchase is True
    mock_review_repo.recalculate_product_stats.assert_called_once_with(product_id)


async def test_submit_review_verified_purchase_false(
    review_svc, mock_review_repo, mock_order_client
):
    """Review submitted with is_verified_purchase=False when order service returns False."""
    user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    mock_order_client.is_verified_purchase.return_value = False
    mock_review_repo.get_by_user_and_product.return_value = None

    saved_review = make_review(
        product_id=product_id,
        user_id=user_id,
        is_verified_purchase=False,
    )
    mock_review_repo.create.return_value = saved_review

    request = SubmitReviewRequest(
        product_id=product_id,
        rating=4,
        title="Good",
        body="Nice product.",
    )
    result = await review_svc.submit_review(user_id, request)

    assert result.is_verified_purchase is False


async def test_submit_review_order_service_unreachable_fail_open(
    review_svc, mock_review_repo, mock_order_client
):
    """When order service is unreachable (returns None), review is allowed but marked unverified."""
    user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    mock_order_client.is_verified_purchase.return_value = None  # unreachable
    mock_review_repo.get_by_user_and_product.return_value = None

    saved_review = make_review(
        product_id=product_id,
        user_id=user_id,
        is_verified_purchase=False,  # fail-open: allow but mark unverified
    )
    mock_review_repo.create.return_value = saved_review

    request = SubmitReviewRequest(
        product_id=product_id,
        rating=3,
        title="Average",
        body="It was okay.",
    )
    result = await review_svc.submit_review(user_id, request)

    # Review was still created (fail-open)
    mock_review_repo.create.assert_called_once()
    assert result.is_verified_purchase is False


async def test_submit_review_duplicate_raises_value_error(
    review_svc, mock_review_repo, mock_order_client
):
    """Submitting a second review for the same product raises ValueError."""
    user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    existing_review = make_review(product_id=product_id, user_id=user_id)
    mock_review_repo.get_by_user_and_product.return_value = existing_review

    request = SubmitReviewRequest(
        product_id=product_id,
        rating=5,
        title="Again",
        body="Trying to review again.",
    )

    with pytest.raises(ValueError, match="already submitted"):
        await review_svc.submit_review(user_id, request)

    # DB create should NOT have been called
    mock_review_repo.create.assert_not_called()


async def test_submit_review_recalculates_rating(
    review_svc, mock_review_repo, mock_order_client
):
    """After review creation, product stats are recalculated."""
    user_id = uuid.uuid4()
    product_id = uuid.uuid4()
    mock_order_client.is_verified_purchase.return_value = True
    mock_review_repo.get_by_user_and_product.return_value = None
    saved_review = make_review(product_id=product_id, user_id=user_id)
    mock_review_repo.create.return_value = saved_review

    request = SubmitReviewRequest(
        product_id=product_id,
        rating=5,
        title="Great",
        body="Loved it.",
    )
    await review_svc.submit_review(user_id, request)

    mock_review_repo.recalculate_product_stats.assert_called_once_with(product_id)


# ---------------------------------------------------------------------------
# delete_review tests
# ---------------------------------------------------------------------------


async def test_delete_review_by_owner_succeeds(review_svc, mock_review_repo):
    user_id = uuid.uuid4()
    review = make_review(user_id=user_id)
    mock_review_repo.get_by_id.return_value = review

    await review_svc.delete_review(
        review.review_id, requesting_user_id=user_id, is_admin=False
    )

    mock_review_repo.delete.assert_called_once_with(review.review_id)
    mock_review_repo.recalculate_product_stats.assert_called_once_with(
        review.product_id
    )


async def test_delete_review_by_admin_succeeds(review_svc, mock_review_repo):
    owner_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    review = make_review(user_id=owner_id)
    mock_review_repo.get_by_id.return_value = review

    # Admin can delete anyone's review
    await review_svc.delete_review(
        review.review_id, requesting_user_id=admin_id, is_admin=True
    )

    mock_review_repo.delete.assert_called_once_with(review.review_id)


async def test_delete_review_by_other_user_raises_permission_error(
    review_svc, mock_review_repo
):
    owner_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    review = make_review(user_id=owner_id)
    mock_review_repo.get_by_id.return_value = review

    with pytest.raises(PermissionError):
        await review_svc.delete_review(
            review.review_id, requesting_user_id=other_user_id, is_admin=False
        )


async def test_delete_review_not_found_raises_lookup_error(
    review_svc, mock_review_repo
):
    mock_review_repo.get_by_id.return_value = None

    with pytest.raises(LookupError):
        await review_svc.delete_review(
            uuid.uuid4(), requesting_user_id=uuid.uuid4(), is_admin=False
        )
