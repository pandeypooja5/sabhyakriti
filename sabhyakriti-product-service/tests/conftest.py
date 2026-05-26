"""Shared pytest fixtures for the product service test suite."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import fakeredis.aioredis
import pytest

from domain.entities.category import Category
from domain.entities.product import Product, ProductImage
from domain.entities.review import Review
from domain.value_objects import CategoryType


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_product(
    *,
    product_id: uuid.UUID | None = None,
    sku: str = "SKU-001",
    name: str = "Banarasi Silk Saree",
    price: Decimal = Decimal("5000.00"),
    discount_percentage: Decimal = Decimal("10.00"),
    stock_qty: int = 20,
    is_active: bool = True,
    average_rating: Decimal = Decimal("4.50"),
    review_count: int = 5,
) -> Product:
    """Factory helper for creating test Product entities."""
    now = _utcnow()
    return Product(
        product_id=product_id or uuid.uuid4(),
        sku=sku,
        name=name,
        slug=name.lower().replace(" ", "-"),
        description="A beautiful Banarasi silk saree.",
        price=price,
        discount_percentage=discount_percentage,
        stock_qty=stock_qty,
        is_active=is_active,
        average_rating=average_rating,
        review_count=review_count,
        created_at=now,
        updated_at=now,
        images=[],
        category_ids=[],
    )


def make_category(
    *,
    category_id: uuid.UUID | None = None,
    name: str = "Silk",
    type: CategoryType = CategoryType.FABRIC,
) -> Category:
    """Factory helper for creating test Category entities."""
    now = _utcnow()
    return Category(
        category_id=category_id or uuid.uuid4(),
        name=name,
        slug=name.lower(),
        type=type,
        display_order=0,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def make_review(
    *,
    review_id: uuid.UUID | None = None,
    product_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    rating: int = 5,
    is_verified_purchase: bool = True,
) -> Review:
    """Factory helper for creating test Review entities."""
    now = _utcnow()
    return Review(
        review_id=review_id or uuid.uuid4(),
        product_id=product_id or uuid.uuid4(),
        user_id=user_id or uuid.uuid4(),
        rating=rating,
        title="Excellent quality!",
        body="The saree is absolutely beautiful and the quality is top-notch.",
        is_verified_purchase=is_verified_purchase,
        created_at=now,
        updated_at=now,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def fake_redis():
    """Provide an async fakeredis instance for testing."""
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield redis
    await redis.aclose()


@pytest.fixture
def mock_order_client():
    """Provide a mock OrderServiceClient."""
    client = MagicMock()
    client.is_verified_purchase = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_product_repo():
    """Provide a mock IProductRepository."""
    repo = MagicMock()
    repo.list_products = AsyncMock(return_value=([], 0))
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_slug = AsyncMock(return_value=None)
    repo.get_slug_set = AsyncMock(return_value=set())
    repo.create = AsyncMock(side_effect=lambda p: p)
    repo.update = AsyncMock()
    repo.soft_delete = AsyncMock()
    repo.reserve_stock = AsyncMock()
    repo.release_stock = AsyncMock()
    repo.get_related_products = AsyncMock(return_value=[])
    repo.slug_exists = AsyncMock(return_value=False)
    return repo


@pytest.fixture
def mock_category_repo():
    """Provide a mock ICategoryRepository."""
    repo = MagicMock()
    repo.list_categories = AsyncMock(return_value=[])
    repo.get_categories_for_product = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_image_repo():
    """Provide a mock IImageRepository."""
    repo = MagicMock()
    repo.list_for_product = AsyncMock(return_value=[])
    repo.count_for_product = AsyncMock(return_value=0)
    repo.clear_primary_flag = AsyncMock()
    repo.create = AsyncMock()
    repo.delete = AsyncMock()
    repo.promote_first_as_primary = AsyncMock()
    return repo


@pytest.fixture
def mock_review_repo():
    """Provide a mock IReviewRepository."""
    repo = MagicMock()
    repo.list_for_product = AsyncMock(return_value=([], 0))
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_user_and_product = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    repo.delete = AsyncMock()
    repo.recalculate_product_stats = AsyncMock()
    return repo


@pytest.fixture
def mock_s3_adapter():
    """Provide a mock AWSS3Adapter."""
    adapter = MagicMock()
    adapter.generate_presigned_put_url = MagicMock(
        return_value="https://s3.example.com/presigned"
    )
    adapter.delete_object = MagicMock()
    return adapter
