"""Unit tests for CartApplicationService.

Uses mocked repositories and product client — no database required.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from application.clients.product_service_client import ProductPriceDTO
from application.services.cart_application_service import CartApplicationService
from domain.value_objects import CouponType
from tests.conftest import make_cart, make_cart_item, make_coupon, make_product_price_dto


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def cart_repo():
    repo = AsyncMock()
    repo.get_item_count = AsyncMock(return_value=0)
    return repo


@pytest.fixture
def wishlist_repo():
    return AsyncMock()


@pytest.fixture
def coupon_repo():
    return AsyncMock()


@pytest.fixture
def product_client():
    return AsyncMock()


@pytest.fixture
def service(cart_repo, wishlist_repo, coupon_repo, product_client):
    return CartApplicationService(
        cart_repo=cart_repo,
        wishlist_repo=wishlist_repo,
        coupon_repo=coupon_repo,
        product_client=product_client,
    )


def _product_map(*product_ids: UUID, price: Decimal = Decimal("999.00")) -> dict:
    return {
        pid: make_product_price_dto(product_id=pid, discounted_price=price)
        for pid in product_ids
    }


# ---------------------------------------------------------------------------
# Flow 2: Add item — creates cart, upserts quantity
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_add_item_creates_cart_and_returns_dto(
    service, cart_repo, product_client
) -> None:
    """Adding an item to a new cart auto-creates the cart and returns CartDTO."""
    user_id = uuid4()
    product_id = uuid4()
    cart = make_cart(user_id=user_id)
    item = make_cart_item(cart_id=cart.cart_id, product_id=product_id, quantity=2)

    cart_repo.get_or_create = AsyncMock(return_value=cart)
    cart_repo.add_item = AsyncMock(return_value=item)
    cart_repo.get_items = AsyncMock(return_value=[item])
    product_client.get_products_batch = AsyncMock(
        return_value=_product_map(product_id)
    )
    service._coupon_repo.find_by_code = AsyncMock(return_value=None)

    result = await service.add_item(user_id, product_id, 2)

    cart_repo.get_or_create.assert_called_once_with(user_id)
    cart_repo.add_item.assert_called_once_with(cart.cart_id, product_id, 2)
    assert result.cart_id == cart.cart_id
    assert len(result.items) == 1
    assert result.items[0].quantity == 2


@pytest.mark.asyncio
async def test_add_same_product_twice_accumulates_quantity(
    service, cart_repo, product_client
) -> None:
    """Adding the same product twice increments quantity via upsert."""
    user_id = uuid4()
    product_id = uuid4()
    cart = make_cart(user_id=user_id)
    # After two adds, the item has quantity=4
    item = make_cart_item(cart_id=cart.cart_id, product_id=product_id, quantity=4)

    cart_repo.get_or_create = AsyncMock(return_value=cart)
    cart_repo.add_item = AsyncMock(return_value=item)
    cart_repo.get_items = AsyncMock(return_value=[item])
    product_client.get_products_batch = AsyncMock(
        return_value=_product_map(product_id)
    )
    service._coupon_repo.find_by_code = AsyncMock(return_value=None)

    # First add
    await service.add_item(user_id, product_id, 2)
    # Second add
    result = await service.add_item(user_id, product_id, 2)

    # add_item should have been called twice on the repo
    assert cart_repo.add_item.call_count == 2
    assert result.items[0].quantity == 4


@pytest.mark.asyncio
async def test_add_21st_product_raises_value_error(
    service, cart_repo
) -> None:
    """Adding a 21st distinct product raises ValueError."""
    user_id = uuid4()
    cart = make_cart(user_id=user_id)

    cart_repo.get_or_create = AsyncMock(return_value=cart)
    # Simulate the repository raising ValueError (enforced at DB level)
    cart_repo.add_item = AsyncMock(
        side_effect=ValueError("Cart cannot have more than 20 distinct products.")
    )

    with pytest.raises(ValueError, match="20 distinct"):
        await service.add_item(user_id, uuid4(), 1)


# ---------------------------------------------------------------------------
# Flow 3: Update quantity — qty=0 removes item
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_set_quantity_zero_removes_item(
    service, cart_repo, product_client
) -> None:
    """Setting quantity=0 removes the item from the cart."""
    user_id = uuid4()
    cart = make_cart(user_id=user_id)
    cart_item_id = uuid4()

    cart_repo.get_or_create = AsyncMock(return_value=cart)
    cart_repo.remove_item = AsyncMock(return_value=True)
    cart_repo.get_items = AsyncMock(return_value=[])
    product_client.get_products_batch = AsyncMock(return_value={})
    service._coupon_repo.find_by_code = AsyncMock(return_value=None)

    result = await service.update_quantity(user_id, cart_item_id, 0)

    cart_repo.remove_item.assert_called_once_with(cart_item_id, cart.cart_id)
    assert result.items == []


@pytest.mark.asyncio
async def test_update_quantity_not_found_raises_lookup_error(
    service, cart_repo
) -> None:
    """Updating a non-existent item raises LookupError."""
    user_id = uuid4()
    cart = make_cart(user_id=user_id)
    cart_repo.get_or_create = AsyncMock(return_value=cart)
    cart_repo.update_item_quantity = AsyncMock(return_value=None)

    with pytest.raises(LookupError, match="not found"):
        await service.update_quantity(user_id, uuid4(), 3)


# ---------------------------------------------------------------------------
# Flow 5: Apply coupon
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_apply_valid_coupon_updates_totals(
    service, cart_repo, coupon_repo, product_client
) -> None:
    """Applying a valid coupon updates the cart totals with discount."""
    user_id = uuid4()
    product_id = uuid4()
    cart = make_cart(user_id=user_id)
    item = make_cart_item(cart_id=cart.cart_id, product_id=product_id, quantity=2)
    coupon = make_coupon(
        code="SAVE200",
        coupon_type=CouponType.FLAT,
        value=Decimal("200"),
        min_order_amount=Decimal("0"),
    )

    cart_repo.get_or_create = AsyncMock(return_value=cart)
    cart_repo.get_items = AsyncMock(return_value=[item])
    cart_repo.apply_coupon = AsyncMock(
        return_value=make_cart(user_id=user_id, applied_coupon_code="SAVE200")
    )
    coupon_repo.find_by_code = AsyncMock(return_value=coupon)
    product_client.get_products_batch = AsyncMock(
        return_value=_product_map(product_id, price=Decimal("1000.00"))
    )

    # After applying, the updated cart is fetched — mock get_items again
    updated_cart = make_cart(user_id=user_id, applied_coupon_code="SAVE200")
    cart_repo.get_or_create = AsyncMock(side_effect=[cart, updated_cart])
    coupon_repo.find_by_code = AsyncMock(side_effect=[coupon, coupon])
    cart_repo.get_items = AsyncMock(return_value=[item])

    result = await service.apply_coupon(user_id, "SAVE200")

    assert result.totals.coupon_code == "SAVE200"
    assert result.totals.discount_amount == Decimal("200.00")


@pytest.mark.asyncio
async def test_apply_expired_coupon_raises_value_error(
    service, cart_repo, coupon_repo, product_client
) -> None:
    """Applying an expired coupon raises ValueError."""
    user_id = uuid4()
    product_id = uuid4()
    cart = make_cart(user_id=user_id)
    item = make_cart_item(cart_id=cart.cart_id, product_id=product_id, quantity=1)
    expired_coupon = make_coupon(
        expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc)
    )

    cart_repo.get_or_create = AsyncMock(return_value=cart)
    cart_repo.get_items = AsyncMock(return_value=[item])
    coupon_repo.find_by_code = AsyncMock(return_value=expired_coupon)
    product_client.get_products_batch = AsyncMock(
        return_value=_product_map(product_id)
    )

    with pytest.raises(ValueError, match="expired"):
        await service.apply_coupon(user_id, expired_coupon.code)


@pytest.mark.asyncio
async def test_apply_nonexistent_coupon_raises_lookup_error(
    service, cart_repo, coupon_repo, product_client
) -> None:
    """Applying a coupon code that doesn't exist raises LookupError."""
    user_id = uuid4()
    cart = make_cart(user_id=user_id)
    cart_repo.get_or_create = AsyncMock(return_value=cart)
    coupon_repo.find_by_code = AsyncMock(return_value=None)

    with pytest.raises(LookupError, match="not found"):
        await service.apply_coupon(user_id, "NOSUCHCODE")


# ---------------------------------------------------------------------------
# Product Service timeout — price_stale flag
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_product_service_timeout_returns_price_stale_flag(
    service, cart_repo, product_client
) -> None:
    """When Product Service times out, price_stale=True is set in the response."""
    user_id = uuid4()
    product_id = uuid4()
    cart = make_cart(user_id=user_id)
    item = make_cart_item(cart_id=cart.cart_id, product_id=product_id, quantity=1)

    cart_repo.get_or_create = AsyncMock(return_value=cart)
    cart_repo.get_items = AsyncMock(return_value=[item])
    # Simulate timeout: client returns empty dict
    product_client.get_products_batch = AsyncMock(return_value={})
    service._coupon_repo.find_by_code = AsyncMock(return_value=None)

    result = await service.get_cart(user_id)

    assert result.totals.price_stale is True


# ---------------------------------------------------------------------------
# Flow 11: Clear cart
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_clear_cart_calls_repo(service, cart_repo) -> None:
    """clear_cart delegates to the repository."""
    user_id = uuid4()
    cart = make_cart(user_id=user_id)
    cart_repo.get_by_user_id = AsyncMock(return_value=cart)
    cart_repo.clear_cart = AsyncMock()

    await service.clear_cart(user_id)

    cart_repo.clear_cart.assert_called_once_with(cart.cart_id)


@pytest.mark.asyncio
async def test_clear_cart_idempotent_when_no_cart(service, cart_repo) -> None:
    """clear_cart is idempotent when no cart exists yet."""
    user_id = uuid4()
    cart_repo.get_by_user_id = AsyncMock(return_value=None)
    cart_repo.clear_cart = AsyncMock()

    await service.clear_cart(user_id)  # Should not raise

    cart_repo.clear_cart.assert_not_called()
