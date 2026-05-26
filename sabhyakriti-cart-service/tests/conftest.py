"""Shared test fixtures for sabhyakriti-cart-service tests."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from application.clients.product_service_client import ProductPriceDTO
from domain.entities.cart import Cart, CartItem
from domain.entities.coupon import Coupon
from domain.value_objects import CouponType


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def make_cart(
    *,
    user_id=None,
    applied_coupon_code=None,
) -> Cart:
    """Create a Cart entity for testing."""
    now = datetime.now(tz=timezone.utc)
    return Cart(
        cart_id=uuid4(),
        user_id=user_id or uuid4(),
        applied_coupon_code=applied_coupon_code,
        created_at=now,
        updated_at=now,
    )


def make_cart_item(
    *,
    cart_id=None,
    product_id=None,
    quantity=1,
) -> CartItem:
    """Create a CartItem entity for testing."""
    return CartItem(
        cart_item_id=uuid4(),
        cart_id=cart_id or uuid4(),
        product_id=product_id or uuid4(),
        quantity=quantity,
        added_at=datetime.now(tz=timezone.utc),
    )


def make_coupon(
    *,
    code="SAVE10",
    coupon_type=CouponType.FLAT,
    value=Decimal("100"),
    min_order_amount=Decimal("0"),
    max_uses=None,
    used_count=0,
    is_active=True,
    expires_at=None,
) -> Coupon:
    """Create a Coupon entity for testing."""
    now = datetime.now(tz=timezone.utc)
    return Coupon(
        coupon_id=uuid4(),
        code=code,
        coupon_type=coupon_type,
        value=value,
        min_order_amount=min_order_amount,
        max_uses=max_uses,
        used_count=used_count,
        is_active=is_active,
        expires_at=expires_at,
        created_at=now,
        updated_at=now,
    )


def make_product_price_dto(
    *,
    product_id=None,
    name="Test Saree",
    primary_image_url=None,
    discounted_price=Decimal("999.00"),
    stock_status="IN_STOCK",
    is_active=True,
) -> ProductPriceDTO:
    """Create a ProductPriceDTO for testing."""
    return ProductPriceDTO(
        product_id=product_id or uuid4(),
        name=name,
        primary_image_url=primary_image_url,
        discounted_price=discounted_price,
        stock_status=stock_status,
        is_active=is_active,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_product_client():
    """Mock ProductServiceClient that returns configurable product data."""
    client = AsyncMock()
    client.get_products_batch = AsyncMock(return_value={})
    return client


@pytest.fixture
def sample_cart():
    """A basic cart for use in tests."""
    return make_cart()


@pytest.fixture
def sample_cart_item(sample_cart):
    """A cart item associated with the sample cart."""
    return make_cart_item(cart_id=sample_cart.cart_id)


@pytest.fixture
def sample_coupon():
    """A valid flat-discount coupon."""
    return make_coupon(code="FLAT100", coupon_type=CouponType.FLAT, value=Decimal("100"))


@pytest.fixture
def sample_percent_coupon():
    """A valid percent-discount coupon."""
    return make_coupon(
        code="SAVE10PCT",
        coupon_type=CouponType.PERCENT,
        value=Decimal("10"),
    )
