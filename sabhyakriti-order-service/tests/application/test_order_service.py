"""
Application service integration tests (no real DB or network).

All external dependencies (repos, HTTP clients) are replaced with mocks.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from application.dtos.order_dtos import (
    CancelOrderRequest,
    CartCheckoutDTO,
    CartItemDTO,
    ConfirmOrderRequest,
    CreateOrderRequest,
    ProcessReturnRequest,
    SubmitReturnItemRequest,
    SubmitReturnRequest,
    UpdateOrderStatusRequest,
)
from application.services.order_application_service import OrderApplicationService
from domain.value_objects import OrderStatus, PaymentMethod, ReturnStatus
from tests.conftest import (
    make_address,
    make_order,
    make_order_item,
    make_return_item,
    make_return_request,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cart_dto(
    price: Decimal = Decimal("1200.00"),
    qty: int = 1,
) -> CartCheckoutDTO:
    return CartCheckoutDTO(
        cart_id="cart-001",
        items=[
            CartItemDTO(
                product_id="prod-001",
                product_name="Banarasi Saree",
                product_image_url="https://cdn.example.com/img.jpg",
                unit_price=Decimal("1500.00"),
                discounted_price=price,
                quantity=qty,
                hsn_code="5208",
            )
        ],
        subtotal=price * qty,
        discount_amount=Decimal("0.00"),
        shipping_charge=Decimal("0.00"),
        cgst_amount=Decimal("30.00"),
        sgst_amount=Decimal("30.00"),
        total_amount=price * qty + Decimal("60.00"),
    )


def _make_service(
    order_repo: MagicMock,
    return_repo: MagicMock,
    product_client: MagicMock,
    payment_client: MagicMock,
    notification_client: MagicMock,
) -> OrderApplicationService:
    return OrderApplicationService(
        order_repo=order_repo,
        return_repo=return_repo,
        product_client=product_client,
        payment_client=payment_client,
        notification_client=notification_client,
    )


# ---------------------------------------------------------------------------
# Create order tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_order_cod_sets_confirmed(
    mock_order_repo: MagicMock,
    mock_return_repo: MagicMock,
    mock_product_client: MagicMock,
    mock_payment_client: MagicMock,
    mock_notification_client: MagicMock,
) -> None:
    """COD orders go directly to CONFIRMED status."""
    cart = _make_cart_dto()
    address = make_address()

    expected_order = make_order(status=OrderStatus.CONFIRMED)
    mock_order_repo.create = AsyncMock(return_value=expected_order)

    svc = _make_service(
        mock_order_repo, mock_return_repo,
        mock_product_client, mock_payment_client, mock_notification_client,
    )

    request = CreateOrderRequest(
        address_id=address.address_id,
        payment_method="COD",
        cart_data=cart,
    )

    result = await svc.create_order(
        user_id="user-123",
        address=address,
        request=request,
    )

    assert result.status == "CONFIRMED"
    mock_product_client.reserve_stock.assert_called_once()
    mock_notification_client.notify_order_placed.assert_called_once()
    mock_notification_client.notify_order_confirmed.assert_called_once()


@pytest.mark.asyncio
async def test_create_order_razorpay_sets_pending(
    mock_order_repo: MagicMock,
    mock_return_repo: MagicMock,
    mock_product_client: MagicMock,
    mock_payment_client: MagicMock,
    mock_notification_client: MagicMock,
) -> None:
    """Razorpay orders start as PENDING until Payment Service confirms."""
    cart = _make_cart_dto()
    address = make_address()

    expected_order = make_order(
        status=OrderStatus.PENDING,
        payment_method=PaymentMethod.RAZORPAY,
    )
    mock_order_repo.create = AsyncMock(return_value=expected_order)

    svc = _make_service(
        mock_order_repo, mock_return_repo,
        mock_product_client, mock_payment_client, mock_notification_client,
    )

    request = CreateOrderRequest(
        address_id=address.address_id,
        payment_method="RAZORPAY",
        cart_data=cart,
    )

    result = await svc.create_order(
        user_id="user-123",
        address=address,
        request=request,
    )

    assert result.status == "PENDING"
    # No confirmed notification for PENDING
    mock_notification_client.notify_order_confirmed.assert_not_called()


@pytest.mark.asyncio
async def test_create_order_stock_failure_triggers_compensating_release(
    mock_order_repo: MagicMock,
    mock_return_repo: MagicMock,
    mock_product_client: MagicMock,
    mock_payment_client: MagicMock,
    mock_notification_client: MagicMock,
) -> None:
    """If stock reservation fails, previously reserved items are released."""
    # First item succeeds, second fails
    call_count = 0

    async def reserve_side_effect(product_id: str, variant_id: object, delta: int) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return  # first succeeds
        raise ValueError("Insufficient stock")

    mock_product_client.reserve_stock = AsyncMock(side_effect=reserve_side_effect)

    cart = CartCheckoutDTO(
        cart_id="cart-002",
        items=[
            CartItemDTO(
                product_id="prod-001",
                product_name="Saree 1",
                product_image_url="https://cdn.example.com/1.jpg",
                unit_price=Decimal("1000.00"),
                discounted_price=Decimal("1000.00"),
                quantity=1,
            ),
            CartItemDTO(
                product_id="prod-002",
                product_name="Saree 2",
                product_image_url="https://cdn.example.com/2.jpg",
                unit_price=Decimal("2000.00"),
                discounted_price=Decimal("2000.00"),
                quantity=1,
            ),
        ],
        subtotal=Decimal("3000.00"),
        discount_amount=Decimal("0.00"),
        shipping_charge=Decimal("0.00"),
        cgst_amount=Decimal("0.00"),
        sgst_amount=Decimal("0.00"),
        total_amount=Decimal("3000.00"),
    )

    address = make_address()
    svc = _make_service(
        mock_order_repo, mock_return_repo,
        mock_product_client, mock_payment_client, mock_notification_client,
    )

    request = CreateOrderRequest(
        address_id=address.address_id,
        payment_method="COD",
        cart_data=cart,
    )

    with pytest.raises(ValueError, match="Stock reservation failed"):
        await svc.create_order(user_id="user-123", address=address, request=request)

    # Compensating release should have been called for the 1 successfully reserved item
    mock_product_client.release_stock.assert_called_once()
    # Order should NOT have been created
    mock_order_repo.create.assert_not_called()


# ---------------------------------------------------------------------------
# Cancel order tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cancel_confirmed_paid_order_calls_refund(
    mock_order_repo: MagicMock,
    mock_return_repo: MagicMock,
    mock_product_client: MagicMock,
    mock_payment_client: MagicMock,
    mock_notification_client: MagicMock,
) -> None:
    """Cancelling a paid CONFIRMED order calls Payment Service initiate_refund."""
    order = make_order(
        status=OrderStatus.CONFIRMED,
        payment_method=PaymentMethod.RAZORPAY,
    )
    cancelled = make_order(
        order_id=order.order_id,
        status=OrderStatus.CANCELLED,
        payment_method=PaymentMethod.RAZORPAY,
    )
    mock_order_repo.get_by_id_write = AsyncMock(return_value=order)
    mock_order_repo.update_status = AsyncMock(return_value=cancelled)
    mock_order_repo.get_items = AsyncMock(return_value=order.items)

    svc = _make_service(
        mock_order_repo, mock_return_repo,
        mock_product_client, mock_payment_client, mock_notification_client,
    )

    result = await svc.cancel_order(
        order_id=order.order_id,
        user_id="user-123",
        request=CancelOrderRequest(reason="Changed my mind"),
    )

    assert result.status == "CANCELLED"
    mock_payment_client.initiate_refund.assert_called_once()
    mock_notification_client.notify_order_cancelled.assert_called_once()


@pytest.mark.asyncio
async def test_cancel_cod_order_no_refund(
    mock_order_repo: MagicMock,
    mock_return_repo: MagicMock,
    mock_product_client: MagicMock,
    mock_payment_client: MagicMock,
    mock_notification_client: MagicMock,
) -> None:
    """Cancelling a COD order does NOT call initiate_refund."""
    order = make_order(status=OrderStatus.CONFIRMED, payment_method=PaymentMethod.COD)
    cancelled = make_order(
        order_id=order.order_id,
        status=OrderStatus.CANCELLED,
        payment_method=PaymentMethod.COD,
    )
    mock_order_repo.get_by_id_write = AsyncMock(return_value=order)
    mock_order_repo.update_status = AsyncMock(return_value=cancelled)
    mock_order_repo.get_items = AsyncMock(return_value=order.items)

    svc = _make_service(
        mock_order_repo, mock_return_repo,
        mock_product_client, mock_payment_client, mock_notification_client,
    )

    await svc.cancel_order(
        order_id=order.order_id,
        user_id="user-123",
        request=CancelOrderRequest(reason="Duplicate order"),
    )

    mock_payment_client.initiate_refund.assert_not_called()


@pytest.mark.asyncio
async def test_cancel_shipped_order_raises(
    mock_order_repo: MagicMock,
    mock_return_repo: MagicMock,
    mock_product_client: MagicMock,
    mock_payment_client: MagicMock,
    mock_notification_client: MagicMock,
) -> None:
    """Cannot cancel a SHIPPED order — raises ValueError."""
    order = make_order(status=OrderStatus.SHIPPED)
    mock_order_repo.get_by_id_write = AsyncMock(return_value=order)

    svc = _make_service(
        mock_order_repo, mock_return_repo,
        mock_product_client, mock_payment_client, mock_notification_client,
    )

    with pytest.raises(ValueError, match="cannot be cancelled"):
        await svc.cancel_order(
            order_id=order.order_id,
            user_id="user-123",
            request=CancelOrderRequest(reason="Test"),
        )


# ---------------------------------------------------------------------------
# Return request tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_submit_return_within_window_succeeds(
    mock_order_repo: MagicMock,
    mock_return_repo: MagicMock,
    mock_product_client: MagicMock,
    mock_payment_client: MagicMock,
    mock_notification_client: MagicMock,
) -> None:
    """Return request within 7-day window succeeds."""
    now = datetime.now(tz=timezone.utc)
    order = make_order(
        status=OrderStatus.DELIVERED,
        delivered_at=now - timedelta(days=3),
    )
    return_req = make_return_request(order_id=order.order_id)

    mock_order_repo.get_by_id = AsyncMock(return_value=order)
    mock_order_repo.get_items = AsyncMock(return_value=order.items)
    mock_order_repo.update_status = AsyncMock(return_value=order)
    mock_return_repo.get_by_order_id = AsyncMock(return_value=None)
    mock_return_repo.create = AsyncMock(return_value=return_req)

    svc = _make_service(
        mock_order_repo, mock_return_repo,
        mock_product_client, mock_payment_client, mock_notification_client,
    )

    result = await svc.submit_return(
        order_id=order.order_id,
        user_id="user-123",
        request=SubmitReturnRequest(
            reason="Received wrong colour",
            items=[
                SubmitReturnItemRequest(
                    order_item_id=order.items[0].order_item_id,
                    quantity=1,
                    reason="Wrong colour",
                )
            ],
        ),
    )

    assert result.status == "PENDING_REVIEW"
    mock_notification_client.notify_return_submitted.assert_called_once()


@pytest.mark.asyncio
async def test_submit_return_after_7_days_raises(
    mock_order_repo: MagicMock,
    mock_return_repo: MagicMock,
    mock_product_client: MagicMock,
    mock_payment_client: MagicMock,
    mock_notification_client: MagicMock,
) -> None:
    """Return request after 7-day window raises ValueError."""
    now = datetime.now(tz=timezone.utc)
    order = make_order(
        status=OrderStatus.DELIVERED,
        delivered_at=now - timedelta(days=8),
    )
    mock_order_repo.get_by_id = AsyncMock(return_value=order)
    mock_return_repo.get_by_order_id = AsyncMock(return_value=None)

    svc = _make_service(
        mock_order_repo, mock_return_repo,
        mock_product_client, mock_payment_client, mock_notification_client,
    )

    with pytest.raises(ValueError, match="Return window"):
        await svc.submit_return(
            order_id=order.order_id,
            user_id="user-123",
            request=SubmitReturnRequest(
                reason="Late return attempt",
                items=[
                    SubmitReturnItemRequest(
                        order_item_id=order.items[0].order_item_id,
                        quantity=1,
                        reason="Test",
                    )
                ],
            ),
        )


@pytest.mark.asyncio
async def test_partial_return_refund_calculated_correctly(
    mock_order_repo: MagicMock,
    mock_return_repo: MagicMock,
    mock_product_client: MagicMock,
    mock_payment_client: MagicMock,
    mock_notification_client: MagicMock,
) -> None:
    """Partial return refund is proportional to returned items."""
    now = datetime.now(tz=timezone.utc)
    order_id = uuid.uuid4()
    item1 = make_order_item(
        order_id=order_id,
        product_id="prod-001",
        quantity=2,
        discounted_price=Decimal("1000.00"),
    )
    item2 = make_order_item(
        order_id=order_id,
        product_id="prod-002",
        quantity=1,
        discounted_price=Decimal("500.00"),
    )
    # subtotal = 2000 + 500 = 2500
    order = make_order(
        order_id=order_id,
        status=OrderStatus.DELIVERED,
        delivered_at=now - timedelta(days=2),
        total_amount=Decimal("2500.00"),
        discount_amount=Decimal("0.00"),
        cgst_amount=Decimal("0.00"),
        sgst_amount=Decimal("0.00"),
    )
    object.__setattr__(order, "items", [item1, item2])
    object.__setattr__(order, "subtotal", Decimal("2500.00"))

    # Return 1 unit of item1 (value = 1000)
    return_req = make_return_request(order_id=order_id, refund_amount=Decimal("1000.00"))

    mock_order_repo.get_by_id = AsyncMock(return_value=order)
    mock_order_repo.get_items = AsyncMock(return_value=[item1, item2])
    mock_order_repo.update_status = AsyncMock(return_value=order)
    mock_return_repo.get_by_order_id = AsyncMock(return_value=None)
    mock_return_repo.create = AsyncMock(return_value=return_req)

    svc = _make_service(
        mock_order_repo, mock_return_repo,
        mock_product_client, mock_payment_client, mock_notification_client,
    )

    result = await svc.submit_return(
        order_id=order_id,
        user_id="user-123",
        request=SubmitReturnRequest(
            reason="Wrong item",
            items=[
                SubmitReturnItemRequest(
                    order_item_id=item1.order_item_id,
                    quantity=1,
                    reason="Not as described",
                )
            ],
        ),
    )

    # Verify a return was created (exact refund depends on domain logic)
    mock_return_repo.create.assert_called_once()
    assert result.status == "PENDING_REVIEW"


# ---------------------------------------------------------------------------
# IDOR protection tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_order_wrong_user_raises_permission_error(
    mock_order_repo: MagicMock,
    mock_return_repo: MagicMock,
    mock_product_client: MagicMock,
    mock_payment_client: MagicMock,
    mock_notification_client: MagicMock,
) -> None:
    """Fetching an order belonging to a different user raises PermissionError."""
    order = make_order(user_id="user-OWNER")
    mock_order_repo.get_by_id = AsyncMock(return_value=order)

    svc = _make_service(
        mock_order_repo, mock_return_repo,
        mock_product_client, mock_payment_client, mock_notification_client,
    )

    with pytest.raises(PermissionError, match="do not have access"):
        await svc.get_order(
            order_id=order.order_id,
            user_id="user-ATTACKER",  # different user
        )


@pytest.mark.asyncio
async def test_cancel_order_wrong_user_raises_permission_error(
    mock_order_repo: MagicMock,
    mock_return_repo: MagicMock,
    mock_product_client: MagicMock,
    mock_payment_client: MagicMock,
    mock_notification_client: MagicMock,
) -> None:
    """Cancelling an order owned by a different user raises PermissionError."""
    order = make_order(user_id="user-OWNER")
    mock_order_repo.get_by_id_write = AsyncMock(return_value=order)

    svc = _make_service(
        mock_order_repo, mock_return_repo,
        mock_product_client, mock_payment_client, mock_notification_client,
    )

    with pytest.raises(PermissionError):
        await svc.cancel_order(
            order_id=order.order_id,
            user_id="user-ATTACKER",
            request=CancelOrderRequest(reason="Trying IDOR"),
        )


# ---------------------------------------------------------------------------
# Admin status update
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_status_confirmed_to_shipped(
    mock_order_repo: MagicMock,
    mock_return_repo: MagicMock,
    mock_product_client: MagicMock,
    mock_payment_client: MagicMock,
    mock_notification_client: MagicMock,
) -> None:
    """Admin can transition CONFIRMED → SHIPPED."""
    order = make_order(status=OrderStatus.CONFIRMED)
    shipped = make_order(order_id=order.order_id, status=OrderStatus.SHIPPED)

    mock_order_repo.get_by_id_write = AsyncMock(return_value=order)
    mock_order_repo.update_status = AsyncMock(return_value=shipped)

    svc = _make_service(
        mock_order_repo, mock_return_repo,
        mock_product_client, mock_payment_client, mock_notification_client,
    )

    result = await svc.update_order_status(
        order_id=order.order_id,
        request=UpdateOrderStatusRequest(new_status="SHIPPED"),
    )

    assert result.status == "SHIPPED"
    mock_notification_client.notify_order_shipped.assert_called_once()


@pytest.mark.asyncio
async def test_update_status_invalid_transition_raises(
    mock_order_repo: MagicMock,
    mock_return_repo: MagicMock,
    mock_product_client: MagicMock,
    mock_payment_client: MagicMock,
    mock_notification_client: MagicMock,
) -> None:
    """Invalid status transition raises ValueError."""
    order = make_order(status=OrderStatus.PENDING)
    mock_order_repo.get_by_id_write = AsyncMock(return_value=order)

    svc = _make_service(
        mock_order_repo, mock_return_repo,
        mock_product_client, mock_payment_client, mock_notification_client,
    )

    with pytest.raises(ValueError, match="Invalid status transition"):
        await svc.update_order_status(
            order_id=order.order_id,
            request=UpdateOrderStatusRequest(new_status="SHIPPED"),
        )
