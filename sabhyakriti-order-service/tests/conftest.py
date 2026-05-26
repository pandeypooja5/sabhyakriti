"""
Shared test fixtures and factory helpers.

Factories produce minimal, fully-typed domain entities for use in unit tests
without requiring a running database or any external service.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from domain.entities.address import Address
from domain.entities.order import Order, OrderItem
from domain.entities.return_request import ReturnItem, ReturnRequest
from domain.value_objects import (
    AddressSnapshot,
    OrderStatus,
    PaymentMethod,
    ReturnStatus,
)


# ---------------------------------------------------------------------------
# Entity factories
# ---------------------------------------------------------------------------


def make_address(
    *,
    user_id: str = "user-123",
    is_default: bool = True,
    address_id: uuid.UUID | None = None,
) -> Address:
    return Address(
        address_id=address_id or uuid.uuid4(),
        user_id=user_id,
        full_name="Priya Sharma",
        phone="9876543210",
        address_line1="12 MG Road",
        address_line2="",
        city="Bengaluru",
        state="Karnataka",
        pincode="560001",
        is_default=is_default,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )


def make_address_snapshot(address: Address | None = None) -> AddressSnapshot:
    addr = address or make_address()
    return AddressSnapshot(
        address_id=str(addr.address_id),
        full_name=addr.full_name,
        phone=addr.phone,
        address_line1=addr.address_line1,
        address_line2=addr.address_line2,
        city=addr.city,
        state=addr.state,
        pincode=addr.pincode,
    )


def make_order_item(
    *,
    order_id: uuid.UUID | None = None,
    product_id: str = "prod-001",
    quantity: int = 2,
    unit_price: Decimal = Decimal("1500.00"),
    discounted_price: Decimal = Decimal("1200.00"),
    order_item_id: uuid.UUID | None = None,
) -> OrderItem:
    oid = order_id or uuid.uuid4()
    return OrderItem(
        order_item_id=order_item_id or uuid.uuid4(),
        order_id=oid,
        product_id=product_id,
        variant_id=None,
        product_name="Banarasi Silk Saree",
        product_image_url="https://cdn.sabhyakriti.in/images/prod-001.jpg",
        unit_price=unit_price,
        discounted_price=discounted_price,
        quantity=quantity,
        hsn_code="5208",
        cgst_rate=Decimal("2.5"),
        sgst_rate=Decimal("2.5"),
        created_at=datetime.now(tz=timezone.utc),
    )


def make_order(
    *,
    user_id: str = "user-123",
    status: OrderStatus = OrderStatus.CONFIRMED,
    payment_method: PaymentMethod = PaymentMethod.COD,
    order_id: uuid.UUID | None = None,
    delivered_at: datetime | None = None,
    total_amount: Decimal = Decimal("2460.00"),
    discount_amount: Decimal = Decimal("240.00"),
    cgst_amount: Decimal = Decimal("60.00"),
    sgst_amount: Decimal = Decimal("60.00"),
) -> Order:
    oid = order_id or uuid.uuid4()
    items = [make_order_item(order_id=oid)]
    return Order(
        order_id=oid,
        user_id=user_id,
        order_number="SKB-202605-000001",
        status=status,
        payment_method=payment_method,
        payment_reference=None,
        shipping_address=make_address_snapshot(),
        subtotal=Decimal("2400.00"),
        discount_amount=discount_amount,
        shipping_charge=Decimal("0.00"),
        cgst_amount=cgst_amount,
        sgst_amount=sgst_amount,
        total_amount=total_amount,
        items=items,
        delivered_at=delivered_at,
        confirmed_at=datetime.now(tz=timezone.utc),
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )


def make_return_item(
    *,
    return_request_id: uuid.UUID | None = None,
    order_item_id: uuid.UUID | None = None,
    quantity: int = 1,
) -> ReturnItem:
    return ReturnItem(
        return_item_id=uuid.uuid4(),
        return_request_id=return_request_id or uuid.uuid4(),
        order_item_id=order_item_id or uuid.uuid4(),
        quantity=quantity,
        reason="Damaged item received",
    )


def make_return_request(
    *,
    order_id: uuid.UUID | None = None,
    user_id: str = "user-123",
    status: ReturnStatus = ReturnStatus.PENDING_REVIEW,
    refund_amount: Decimal = Decimal("1200.00"),
) -> ReturnRequest:
    rr_id = uuid.uuid4()
    oid = order_id or uuid.uuid4()
    return ReturnRequest(
        return_request_id=rr_id,
        order_id=oid,
        user_id=user_id,
        status=status,
        reason="Received damaged product",
        items=[make_return_item(return_request_id=rr_id)],
        refund_amount=refund_amount,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )


# ---------------------------------------------------------------------------
# Mock client fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_product_client() -> MagicMock:
    client = MagicMock()
    client.reserve_stock = AsyncMock(return_value=None)
    client.release_stock = AsyncMock(return_value=None)
    return client


@pytest.fixture
def mock_payment_client() -> MagicMock:
    client = MagicMock()
    client.initiate_refund = AsyncMock(return_value={"refund_id": "ref-001"})
    client.cancel_pending_payment = AsyncMock(return_value=None)
    return client


@pytest.fixture
def mock_notification_client() -> MagicMock:
    client = MagicMock()
    client.notify_order_placed = MagicMock(return_value=None)
    client.notify_order_confirmed = MagicMock(return_value=None)
    client.notify_order_shipped = MagicMock(return_value=None)
    client.notify_order_delivered = MagicMock(return_value=None)
    client.notify_order_cancelled = MagicMock(return_value=None)
    client.notify_return_submitted = MagicMock(return_value=None)
    client.notify_return_approved = MagicMock(return_value=None)
    client.notify_return_rejected = MagicMock(return_value=None)
    client.notify_refund_initiated = MagicMock(return_value=None)
    return client


@pytest.fixture
def mock_order_repo() -> MagicMock:
    repo = MagicMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_id_write = AsyncMock()
    repo.list_by_user = AsyncMock(return_value=([], 0))
    repo.list_all = AsyncMock(return_value=([], 0))
    repo.update_status = AsyncMock()
    repo.get_items = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_return_repo() -> MagicMock:
    repo = MagicMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_order_id = AsyncMock(return_value=None)
    repo.update_status = AsyncMock()
    repo.list_all = AsyncMock(return_value=([], 0))
    return repo


@pytest.fixture
def mock_address_repo() -> MagicMock:
    repo = MagicMock()
    repo.list_by_user = AsyncMock(return_value=[])
    repo.get_by_id = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.set_default = AsyncMock()
    repo.count_by_user = AsyncMock(return_value=0)
    return repo
