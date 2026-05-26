"""Unit tests for PaymentApplicationService — all 7 business flows."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from application.dtos.payment_dtos import (
    CODConfirmRequest,
    RefundRequest,
    VerifyPaymentRequest,
)
from application.services.payment_application_service import PaymentApplicationService
from domain.value_objects import PaymentMethod, PaymentStatus
from tests.conftest import (
    TEST_KEY_SECRET,
    TEST_WEBHOOK_SECRET,
    make_payment,
    make_webhook_event,
    sign_payment,
    sign_webhook,
)


# ---------------------------------------------------------------------------
# Flow 1 — Create Razorpay order
# ---------------------------------------------------------------------------


async def test_create_razorpay_order_success(
    payment_service: PaymentApplicationService,
    mock_payment_repo: AsyncMock,
    mock_razorpay_adapter: AsyncMock,
) -> None:
    """Happy path: Razorpay adapter called; payment created with CREATED status."""
    order_id = uuid4()
    user_id = uuid4()

    result = await payment_service.create_razorpay_order(
        order_id=order_id,
        user_id=user_id,
        amount=Decimal("999.00"),
    )

    mock_razorpay_adapter.create_order.assert_awaited_once()
    mock_payment_repo.create.assert_awaited_once()

    created_payment = mock_payment_repo.create.call_args[0][0]
    assert created_payment.status == PaymentStatus.CREATED
    assert created_payment.order_id == order_id
    assert result.razorpay_order_id == "order_rz123"
    assert result.amount == 99900


async def test_create_razorpay_order_already_paid_raises(
    payment_service: PaymentApplicationService,
    mock_payment_repo: AsyncMock,
) -> None:
    """Creating an order for an already-captured payment raises ValueError."""
    captured = make_payment(status=PaymentStatus.CAPTURED)
    mock_payment_repo.get_by_order_id.return_value = captured

    with pytest.raises(ValueError, match="already paid"):
        await payment_service.create_razorpay_order(
            order_id=captured.order_id,
            user_id=captured.user_id,
            amount=Decimal("999.00"),
        )


async def test_create_razorpay_order_max_attempts_exceeded(
    payment_service: PaymentApplicationService,
    mock_payment_repo: AsyncMock,
) -> None:
    """Exceeding 3 attempts raises ValueError."""
    existing = make_payment(status=PaymentStatus.CREATED, attempt_count=3)
    mock_payment_repo.get_by_order_id.return_value = existing

    with pytest.raises(ValueError, match="Maximum"):
        await payment_service.create_razorpay_order(
            order_id=existing.order_id,
            user_id=existing.user_id,
            amount=Decimal("999.00"),
        )


# ---------------------------------------------------------------------------
# Flow 2 — Verify payment
# ---------------------------------------------------------------------------


async def test_verify_payment_valid_signature_captures(
    payment_service: PaymentApplicationService,
    mock_payment_repo: AsyncMock,
    mock_order_client: AsyncMock,
) -> None:
    """Valid signature transitions the payment to CAPTURED and notifies Order Service."""
    rz_order_id = "order_abc"
    rz_payment_id = "pay_abc"
    payment = make_payment(
        status=PaymentStatus.CREATED,
        razorpay_order_id=rz_order_id,
    )
    mock_payment_repo.get_by_order_id.return_value = payment

    sig = sign_payment(TEST_KEY_SECRET, rz_order_id, rz_payment_id)
    req = VerifyPaymentRequest(
        order_id=payment.order_id,
        razorpay_payment_id=rz_payment_id,
        razorpay_order_id=rz_order_id,
        razorpay_signature=sig,
    )

    result = await payment_service.verify_payment(req)

    mock_payment_repo.update.assert_awaited_once()
    updated = mock_payment_repo.update.call_args[0][0]
    assert updated.status == PaymentStatus.CAPTURED
    assert updated.razorpay_payment_id == rz_payment_id
    assert updated.captured_at is not None
    mock_order_client.confirm_order.assert_awaited_once_with(payment.order_id)
    assert result.status == PaymentStatus.CAPTURED


async def test_verify_payment_invalid_signature_raises(
    payment_service: PaymentApplicationService,
    mock_payment_repo: AsyncMock,
) -> None:
    """Invalid signature raises ValueError and marks payment FAILED."""
    payment = make_payment(status=PaymentStatus.CREATED, razorpay_order_id="order_x")
    mock_payment_repo.get_by_order_id.return_value = payment

    req = VerifyPaymentRequest(
        order_id=payment.order_id,
        razorpay_payment_id="pay_x",
        razorpay_order_id="order_x",
        razorpay_signature="invalid_signature_value",
    )

    with pytest.raises(ValueError, match="signature verification failed"):
        await payment_service.verify_payment(req)

    updated = mock_payment_repo.update.call_args[0][0]
    assert updated.status == PaymentStatus.FAILED


async def test_verify_payment_already_captured_raises_409_equivalent(
    payment_service: PaymentApplicationService,
    mock_payment_repo: AsyncMock,
) -> None:
    """Attempting to verify an already-captured payment raises ValueError (409-equivalent)."""
    payment = make_payment(
        status=PaymentStatus.CAPTURED,
        razorpay_payment_id="pay_already",
    )
    mock_payment_repo.get_by_order_id.return_value = payment

    req = VerifyPaymentRequest(
        order_id=payment.order_id,
        razorpay_payment_id="pay_already",
        razorpay_order_id="order_x",
        razorpay_signature="any_sig",
    )

    with pytest.raises(ValueError, match="already captured"):
        await payment_service.verify_payment(req)


# ---------------------------------------------------------------------------
# Flow 3 — COD confirm
# ---------------------------------------------------------------------------


async def test_confirm_cod_payment_creates_captured_immediately(
    payment_service: PaymentApplicationService,
    mock_payment_repo: AsyncMock,
) -> None:
    """COD payment is created with CAPTURED status — no Razorpay call."""
    req = CODConfirmRequest(
        order_id=uuid4(),
        amount=Decimal("499.00"),
        user_id=uuid4(),
    )

    result = await payment_service.confirm_cod_payment(req)

    mock_payment_repo.create.assert_awaited_once()
    created = mock_payment_repo.create.call_args[0][0]
    assert created.status == PaymentStatus.CAPTURED
    assert created.method == PaymentMethod.COD
    assert created.captured_at is not None
    assert result.status == PaymentStatus.CAPTURED


async def test_confirm_cod_payment_duplicate_raises(
    payment_service: PaymentApplicationService,
    mock_payment_repo: AsyncMock,
) -> None:
    """Duplicate COD confirm raises ValueError."""
    existing = make_payment(status=PaymentStatus.CAPTURED, method=PaymentMethod.COD)
    mock_payment_repo.get_by_order_id.return_value = existing

    req = CODConfirmRequest(
        order_id=existing.order_id,
        amount=existing.amount,
        user_id=existing.user_id,
    )

    with pytest.raises(ValueError, match="already exists"):
        await payment_service.confirm_cod_payment(req)


# ---------------------------------------------------------------------------
# Flow 4 — Process webhook
# ---------------------------------------------------------------------------


async def test_process_webhook_payment_captured_transitions_and_confirms_order(
    payment_service: PaymentApplicationService,
    mock_payment_repo: AsyncMock,
    mock_webhook_repo: AsyncMock,
    mock_order_client: AsyncMock,
) -> None:
    """payment.captured webhook: payment transitions to CAPTURED, order confirmed."""
    rz_payment_id = "pay_wh001"
    payment = make_payment(status=PaymentStatus.CREATED, razorpay_order_id="order_wh001")
    mock_payment_repo.get_by_razorpay_payment_id.return_value = payment

    event_id = "evt_wh001"
    payload = {
        "id": event_id,
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": rz_payment_id,
                    "order_id": "order_wh001",
                    "status": "captured",
                }
            }
        },
    }
    raw_body = json.dumps(payload).encode()
    sig = sign_webhook(TEST_WEBHOOK_SECRET, raw_body)

    event = make_webhook_event(razorpay_event_id=event_id, event_type="payment.captured")
    mock_webhook_repo.create_if_not_exists.return_value = (event, True)

    await payment_service.process_webhook(raw_body, sig)

    mock_payment_repo.update.assert_awaited()
    updated = mock_payment_repo.update.call_args[0][0]
    assert updated.status == PaymentStatus.CAPTURED
    mock_order_client.confirm_order.assert_awaited_once_with(payment.order_id)
    mock_webhook_repo.mark_processed.assert_awaited_once_with(event_id)


async def test_process_webhook_invalid_signature_raises(
    payment_service: PaymentApplicationService,
) -> None:
    """Invalid webhook signature raises ValueError immediately."""
    payload = {"id": "evt_bad", "event": "payment.captured"}
    raw_body = json.dumps(payload).encode()

    with pytest.raises(ValueError, match="signature"):
        await payment_service.process_webhook(raw_body, "bad_signature")


# ---------------------------------------------------------------------------
# Flow 5 — Initiate refund
# ---------------------------------------------------------------------------


async def test_initiate_refund_captured_payment_calls_razorpay(
    payment_service: PaymentApplicationService,
    mock_payment_repo: AsyncMock,
    mock_razorpay_adapter: AsyncMock,
) -> None:
    """Refund on a CAPTURED payment calls Razorpay and marks payment REFUNDED."""
    payment = make_payment(
        status=PaymentStatus.CAPTURED,
        razorpay_payment_id="pay_cap001",
        captured_at=datetime.now(tz=timezone.utc),
    )
    mock_payment_repo.get_by_order_id.return_value = payment

    req = RefundRequest(order_id=payment.order_id, amount=Decimal("999.00"))
    result = await payment_service.initiate_refund(req)

    mock_razorpay_adapter.create_refund.assert_awaited_once_with("pay_cap001", 99900)
    updated = mock_payment_repo.update.call_args[0][0]
    assert updated.status == PaymentStatus.REFUNDED
    assert updated.refund_id == "rfnd_test123"
    assert result.refund_id == "rfnd_test123"


async def test_initiate_refund_non_captured_raises(
    payment_service: PaymentApplicationService,
    mock_payment_repo: AsyncMock,
) -> None:
    """Refunding a non-CAPTURED payment raises ValueError."""
    payment = make_payment(status=PaymentStatus.CREATED)
    mock_payment_repo.get_by_order_id.return_value = payment

    req = RefundRequest(order_id=payment.order_id, amount=Decimal("100.00"))

    with pytest.raises(ValueError, match="not refundable"):
        await payment_service.initiate_refund(req)


# ---------------------------------------------------------------------------
# Flow 6 — Get payment receipt
# ---------------------------------------------------------------------------


async def test_get_payment_receipt_idor_check(
    payment_service: PaymentApplicationService,
    mock_payment_repo: AsyncMock,
) -> None:
    """IDOR: a different user cannot retrieve the receipt for someone else's order."""
    owner_id = uuid4()
    attacker_id = uuid4()
    payment = make_payment(
        status=PaymentStatus.CAPTURED,
        captured_at=datetime.now(tz=timezone.utc),
    )
    payment.user_id = owner_id
    mock_payment_repo.get_by_order_id.return_value = payment

    with pytest.raises(PermissionError):
        await payment_service.get_payment_receipt(
            user_id=attacker_id,
            order_id=payment.order_id,
        )


async def test_get_payment_receipt_success(
    payment_service: PaymentApplicationService,
    mock_payment_repo: AsyncMock,
    mock_order_client: AsyncMock,
) -> None:
    """Owner gets a valid receipt for a captured payment."""
    user_id = uuid4()
    payment = make_payment(
        status=PaymentStatus.CAPTURED,
        captured_at=datetime.now(tz=timezone.utc),
    )
    payment.user_id = user_id
    mock_payment_repo.get_by_order_id.return_value = payment
    mock_order_client.get_order_number.return_value = "ORD-2026-001"

    receipt = await payment_service.get_payment_receipt(
        user_id=user_id,
        order_id=payment.order_id,
    )

    assert receipt.status == PaymentStatus.CAPTURED
    assert receipt.order_number == "ORD-2026-001"


# ---------------------------------------------------------------------------
# Flow 7 — Cancel stale payments
# ---------------------------------------------------------------------------


async def test_cancel_stale_payments_cancels_and_notifies_order_service(
    payment_service: PaymentApplicationService,
    mock_payment_repo: AsyncMock,
    mock_order_client: AsyncMock,
) -> None:
    """Stale CREATED payments are cancelled and Order Service is notified."""
    stale_payment = make_payment(
        status=PaymentStatus.CREATED,
        first_attempt_at=datetime.now(tz=timezone.utc) - timedelta(minutes=35),
    )
    mock_payment_repo.list_stale_created.return_value = [stale_payment]

    count = await payment_service.cancel_stale_payments()

    assert count == 1
    updated = mock_payment_repo.update.call_args[0][0]
    assert updated.status == PaymentStatus.CANCELLED
    mock_order_client.cancel_order.assert_awaited_once()
    _, kwargs = mock_order_client.cancel_order.call_args
    # order_id passed as positional arg
    assert mock_order_client.cancel_order.call_args[0][0] == stale_payment.order_id


async def test_cancel_stale_payments_no_stale(
    payment_service: PaymentApplicationService,
    mock_payment_repo: AsyncMock,
    mock_order_client: AsyncMock,
) -> None:
    """When no stale payments exist, nothing is cancelled."""
    mock_payment_repo.list_stale_created.return_value = []

    count = await payment_service.cancel_stale_payments()

    assert count == 0
    mock_order_client.cancel_order.assert_not_called()
