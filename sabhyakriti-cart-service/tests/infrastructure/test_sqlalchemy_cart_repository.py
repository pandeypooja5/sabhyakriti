"""Infrastructure tests for SQLAlchemyCartRepository.

Tests upsert logic, unique constraints, clear_cart, and item count.
These are unit tests using AsyncMock sessions (no live DB required).
For integration tests with a real DB, see conftest_integration.py (optional).
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from domain.entities.cart import Cart, CartItem
from infrastructure.persistence.repositories.sqlalchemy_cart_repository import (
    SQLAlchemyCartRepository,
    _item_model_to_entity,
    _model_to_entity,
)
from infrastructure.persistence.models import CartModel, CartItemModel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cart_model(user_id=None, coupon=None) -> CartModel:
    now = datetime.now(tz=timezone.utc)
    m = CartModel()
    m.cart_id = uuid4()
    m.user_id = user_id or uuid4()
    m.applied_coupon_code = coupon
    m.created_at = now
    m.updated_at = now
    return m


def _make_item_model(cart_id=None, product_id=None, quantity=1) -> CartItemModel:
    m = CartItemModel()
    m.cart_item_id = uuid4()
    m.cart_id = cart_id or uuid4()
    m.product_id = product_id or uuid4()
    m.quantity = quantity
    m.added_at = datetime.now(tz=timezone.utc)
    return m


# ---------------------------------------------------------------------------
# Mapper tests
# ---------------------------------------------------------------------------

def test_model_to_entity_maps_fields() -> None:
    """_model_to_entity maps all CartModel fields to Cart entity."""
    model = _make_cart_model(coupon="SAVE10")
    entity = _model_to_entity(model)
    assert entity.cart_id == model.cart_id
    assert entity.user_id == model.user_id
    assert entity.applied_coupon_code == "SAVE10"


def test_item_model_to_entity_maps_fields() -> None:
    """_item_model_to_entity maps all CartItemModel fields to CartItem entity."""
    model = _make_item_model(quantity=5)
    entity = _item_model_to_entity(model)
    assert entity.cart_item_id == model.cart_item_id
    assert entity.quantity == 5


# ---------------------------------------------------------------------------
# get_or_create tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_or_create_returns_existing_cart() -> None:
    """get_or_create returns existing cart without creating a new one."""
    session = AsyncMock()
    model = _make_cart_model()

    execute_result = MagicMock()
    execute_result.scalar_one_or_none = MagicMock(return_value=model)
    session.execute = AsyncMock(return_value=execute_result)

    repo = SQLAlchemyCartRepository(session)
    cart = await repo.get_or_create(model.user_id)

    assert cart.cart_id == model.cart_id
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_get_or_create_creates_new_cart_when_none_exists() -> None:
    """get_or_create inserts new cart when user has none."""
    session = AsyncMock()

    # First call returns None (no existing cart)
    execute_result = MagicMock()
    execute_result.scalar_one_or_none = MagicMock(return_value=None)
    session.execute = AsyncMock(return_value=execute_result)
    session.flush = AsyncMock()

    repo = SQLAlchemyCartRepository(session)
    user_id = uuid4()

    # Patch CartModel to capture what was added
    added_models = []
    original_add = session.add
    session.add = MagicMock(side_effect=lambda m: added_models.append(m))

    cart = await repo.get_or_create(user_id)

    session.add.assert_called_once()
    assert cart.user_id == user_id


# ---------------------------------------------------------------------------
# add_item: max product constraint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_add_item_raises_when_max_products_exceeded() -> None:
    """add_item raises ValueError when cart already has 20 distinct products."""
    session = AsyncMock()
    cart_id = uuid4()
    product_id = uuid4()

    # No existing item for this product
    no_existing = MagicMock()
    no_existing.scalar_one_or_none = MagicMock(return_value=None)

    # Item count returns 20 (at the limit)
    count_result = MagicMock()
    count_result.scalar_one = MagicMock(return_value=20)

    session.execute = AsyncMock(side_effect=[no_existing, count_result])

    repo = SQLAlchemyCartRepository(session)

    with pytest.raises(ValueError, match="20 distinct"):
        await repo.add_item(cart_id, product_id, 1)


# ---------------------------------------------------------------------------
# add_item: max quantity constraint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_add_item_raises_when_quantity_exceeds_10() -> None:
    """add_item raises ValueError when quantity would exceed 10."""
    session = AsyncMock()
    cart_id = uuid4()
    product_id = uuid4()

    # Existing item with quantity=8
    existing = _make_item_model(cart_id=cart_id, product_id=product_id, quantity=8)
    existing_result = MagicMock()
    existing_result.scalar_one_or_none = MagicMock(return_value=existing)
    session.execute = AsyncMock(return_value=existing_result)

    repo = SQLAlchemyCartRepository(session)

    with pytest.raises(ValueError, match="maximum quantity"):
        await repo.add_item(cart_id, product_id, 3)  # 8 + 3 = 11 > 10


# ---------------------------------------------------------------------------
# clear_cart: idempotent
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_clear_cart_deletes_items_and_clears_coupon() -> None:
    """clear_cart executes DELETE on items and UPDATE on cart (coupon=None)."""
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock())
    session.flush = AsyncMock()

    repo = SQLAlchemyCartRepository(session)
    cart_id = uuid4()

    await repo.clear_cart(cart_id)

    # Two executes: DELETE items + UPDATE cart coupon
    assert session.execute.call_count == 2


# ---------------------------------------------------------------------------
# Unique constraint: same product upserts quantity
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_add_item_increments_existing_quantity() -> None:
    """Adding a product already in cart increments quantity (upsert)."""
    session = AsyncMock()
    cart_id = uuid4()
    product_id = uuid4()

    existing = _make_item_model(cart_id=cart_id, product_id=product_id, quantity=3)
    existing_result = MagicMock()
    existing_result.scalar_one_or_none = MagicMock(return_value=existing)

    # For the UPDATE execute + flush
    update_result = MagicMock()
    session.execute = AsyncMock(side_effect=[existing_result, update_result])
    session.flush = AsyncMock()
    session.refresh = AsyncMock()

    repo = SQLAlchemyCartRepository(session)
    item = await repo.add_item(cart_id, product_id, 2)  # 3 + 2 = 5

    # The update should have been called (second execute call)
    assert session.execute.call_count == 2


@pytest.mark.asyncio
async def test_get_item_count_returns_distinct_count() -> None:
    """get_item_count returns the number of distinct products."""
    session = AsyncMock()
    count_result = MagicMock()
    count_result.scalar_one = MagicMock(return_value=5)
    session.execute = AsyncMock(return_value=count_result)

    repo = SQLAlchemyCartRepository(session)
    count = await repo.get_item_count(uuid4())

    assert count == 5
