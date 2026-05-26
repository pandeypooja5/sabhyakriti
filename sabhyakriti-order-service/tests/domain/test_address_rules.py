"""
Address business rules tests.

Covers:
- Max 5 addresses per user
- First address auto-set as default
- Deleting default promotes next address
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from application.dtos.order_dtos import CreateAddressRequest
from application.services.address_application_service import (
    MAX_ADDRESSES_PER_USER,
    AddressApplicationService,
)
from domain.entities.address import Address
from tests.conftest import make_address


def _make_service(count: int = 0) -> tuple[AddressApplicationService, MagicMock]:
    repo = MagicMock()
    repo.count_by_user = AsyncMock(return_value=count)
    repo.create = AsyncMock(side_effect=lambda a: a)
    repo.list_by_user = AsyncMock(return_value=[])
    repo.get_by_id = AsyncMock()
    repo.update = AsyncMock(side_effect=lambda a: a)
    repo.delete = AsyncMock()
    repo.set_default = AsyncMock(side_effect=lambda aid, uid: make_address(
        address_id=aid, is_default=True
    ))
    svc = AddressApplicationService(address_repo=repo)
    return svc, repo


def _create_request() -> CreateAddressRequest:
    return CreateAddressRequest(
        full_name="Test User",
        phone="9876543210",
        address_line1="123 Test Street",
        city="Mumbai",
        state="Maharashtra",
        pincode="400001",
    )


# ---------------------------------------------------------------------------
# Max 5 addresses
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_address_enforces_max_5() -> None:
    svc, _ = _make_service(count=MAX_ADDRESSES_PER_USER)
    with pytest.raises(ValueError, match="Maximum 5 addresses"):
        await svc.add_address(user_id="user-1", request=_create_request())


@pytest.mark.asyncio
async def test_add_address_allows_exactly_5() -> None:
    """Adding the 5th address succeeds."""
    svc, repo = _make_service(count=4)  # 4 existing, adding 5th
    addr = await svc.add_address(user_id="user-1", request=_create_request())
    repo.create.assert_called_once()
    # 5th address is not auto-default (only 1st is)
    assert addr.is_default is False


# ---------------------------------------------------------------------------
# Auto-default on first address
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_first_address_auto_default() -> None:
    """The first address added for a user is automatically set as default."""
    svc, repo = _make_service(count=0)
    addr = await svc.add_address(user_id="user-1", request=_create_request())
    assert addr.is_default is True


@pytest.mark.asyncio
async def test_second_address_not_auto_default() -> None:
    """Subsequent addresses are not auto-default."""
    svc, repo = _make_service(count=1)
    addr = await svc.add_address(user_id="user-1", request=_create_request())
    assert addr.is_default is False


# ---------------------------------------------------------------------------
# Default promotion on delete
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_calls_repository() -> None:
    """Deleting an address calls the repository delete method."""
    svc, repo = _make_service()
    address_id = uuid.uuid4()
    existing = make_address(address_id=address_id, is_default=True)
    repo.get_by_id = AsyncMock(return_value=existing)

    await svc.delete_address(address_id=address_id, user_id="user-1")

    repo.delete.assert_called_once_with(address_id, "user-1")


@pytest.mark.asyncio
async def test_delete_nonexistent_address_raises() -> None:
    """Deleting a non-existent address raises ValueError."""
    svc, repo = _make_service()
    repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(ValueError, match="not found"):
        await svc.delete_address(address_id=uuid.uuid4(), user_id="user-1")


# ---------------------------------------------------------------------------
# Set default
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_default_calls_repository() -> None:
    """set_default delegates to repository and returns updated address."""
    svc, repo = _make_service()
    address_id = uuid.uuid4()
    existing = make_address(address_id=address_id, is_default=False)
    repo.get_by_id = AsyncMock(return_value=existing)

    result = await svc.set_default(address_id=address_id, user_id="user-1")

    repo.set_default.assert_called_once_with(address_id, "user-1")
    assert result.is_default is True


@pytest.mark.asyncio
async def test_set_default_nonexistent_raises() -> None:
    svc, repo = _make_service()
    repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(ValueError, match="not found"):
        await svc.set_default(address_id=uuid.uuid4(), user_id="user-1")
