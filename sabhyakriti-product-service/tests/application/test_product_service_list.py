"""Tests for ProductApplicationService.list_products — cache hit/miss/invalidation."""
from __future__ import annotations

import json
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import fakeredis.aioredis
import pytest

from application.services.product_application_service import ProductApplicationService
from domain.value_objects import SortOrder
from infrastructure.cache.plp_cache_repository import PlpCacheRepository
from tests.conftest import make_product


@pytest.fixture
async def redis_client():
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield r
    await r.aclose()


@pytest.fixture
def plp_cache(redis_client):
    return PlpCacheRepository(redis_client)


@pytest.fixture
def product_svc(
    mock_product_repo,
    mock_category_repo,
    mock_image_repo,
    mock_review_repo,
    plp_cache,
    mock_s3_adapter,
):
    return ProductApplicationService(
        product_repo=mock_product_repo,
        category_repo=mock_category_repo,
        image_repo=mock_image_repo,
        review_repo=mock_review_repo,
        plp_cache=plp_cache,
        s3_adapter=mock_s3_adapter,
        cloudfront_domain="d123.cloudfront.net",
        s3_bucket="test-bucket",
    )


async def test_list_products_cache_miss_calls_db(
    product_svc, mock_product_repo, redis_client
):
    """On cache miss, the repository should be called and result cached."""
    product = make_product()
    mock_product_repo.list_products.return_value = ([product], 1)

    result = await product_svc.list_products(page=1, page_size=24)

    # DB was called
    mock_product_repo.list_products.assert_called_once()
    assert result.total_count == 1
    assert len(result.items) == 1

    # Result was cached in Redis
    keys = await redis_client.keys("product_plp:*")
    assert len(keys) == 1


async def test_list_products_cache_hit_skips_db(
    product_svc, mock_product_repo, redis_client
):
    """On cache hit, the repository must NOT be called."""
    product = make_product()
    mock_product_repo.list_products.return_value = ([product], 1)

    # First call: populate cache
    await product_svc.list_products(page=1, page_size=24)
    assert mock_product_repo.list_products.call_count == 1

    # Second call with same params: should hit cache
    result2 = await product_svc.list_products(page=1, page_size=24)
    assert mock_product_repo.list_products.call_count == 1  # Not called again

    assert result2.total_count == 1


async def test_list_products_different_params_separate_cache_keys(
    product_svc, mock_product_repo
):
    """Different query params produce different cache keys."""
    product = make_product()
    mock_product_repo.list_products.return_value = ([product], 1)

    await product_svc.list_products(page=1, page_size=24)
    await product_svc.list_products(page=2, page_size=24)
    await product_svc.list_products(page=1, page_size=12)

    # Each unique set of params calls DB once
    assert mock_product_repo.list_products.call_count == 3


async def test_cache_invalidated_on_create_product(
    product_svc, mock_product_repo, mock_category_repo, mock_image_repo,
    mock_review_repo, redis_client
):
    """Creating a product must flush all PLP cache entries."""
    product = make_product()
    mock_product_repo.list_products.return_value = ([product], 1)
    mock_product_repo.get_related_products.return_value = []

    # Populate cache
    await product_svc.list_products(page=1, page_size=24)
    keys_before = await redis_client.keys("product_plp:*")
    assert len(keys_before) == 1

    # Create a product (triggers cache invalidation)
    from application.dtos.product_dtos import CreateProductRequest

    saved_product = make_product(name="New Saree")
    mock_product_repo.create.return_value = saved_product
    mock_product_repo.get_by_id.return_value = saved_product
    mock_product_repo.get_slug_set.return_value = set()

    request = CreateProductRequest(
        sku="NEW-001",
        name="New Saree",
        price=Decimal("3000.00"),
        discount_percentage=Decimal("5.00"),
        stock_qty=10,
    )
    await product_svc.create_product(request)

    # Cache must be cleared
    keys_after = await redis_client.keys("product_plp:*")
    assert len(keys_after) == 0


async def test_cache_invalidated_on_soft_delete(
    product_svc, mock_product_repo, redis_client
):
    """Soft deleting a product must flush all PLP cache entries."""
    product = make_product()
    mock_product_repo.list_products.return_value = ([product], 1)

    await product_svc.list_products(page=1, page_size=24)
    keys_before = await redis_client.keys("product_plp:*")
    assert len(keys_before) == 1

    await product_svc.soft_delete_product(product.product_id)

    keys_after = await redis_client.keys("product_plp:*")
    assert len(keys_after) == 0


async def test_list_products_page_size_capped_at_48(
    product_svc, mock_product_repo
):
    """page_size > 48 must be capped to 48."""
    mock_product_repo.list_products.return_value = ([], 0)

    await product_svc.list_products(page=1, page_size=100)

    call_kwargs = mock_product_repo.list_products.call_args.kwargs
    assert call_kwargs["page_size"] == 48
