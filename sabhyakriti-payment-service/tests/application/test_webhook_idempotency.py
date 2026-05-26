"""Explicit idempotency tests for webhook processing.

Verifies that submitting the same Razorpay webhook event twice results in
the Order Service being contacted exactly once (not twice).
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from application.services.payment_application_service import PaymentApplicationService
from domain.value_objects import PaymentStatus
from tests.conftest import (
    TEST_WEBHOOK_SECRET,
    make_payment,
    make_webhook_event,
    sign_webhook,
)


def _make_captured_payload(event_id: str, rz_payment_id: str) -> bytes:
    payload = {
        "id": event_id,
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": rz_payment_id,
                    "order_id": "order_idem001",
                    "status": "captured",
                }
            }
        },
    }
    return json.dumps(payload).encode()


async def test_duplicate_webhook_order_service_called_exactly_once(
    payment_service: PaymentApplicationService,
    mock_payment_repo: AsyncMock,
    mock_webhook_repo: AsyncMock,
    mock_order_client: AsyncMock,
) -> None:
    """Sending the same webhook event twice triggers Order Service confirm exactly once.

    First call: create_if_not_exists returns (event, True) — is_new=True → process.
    Second call: create_if_not_exists returns (event, False) — is_new=False → skip.
    """
    event_id = "evt_idem001"
    rz_payment_id = "pay_idem001"
    raw_body = _make_captured_payload(event_id, rz_payment_id)
    sig = sign_webhook(TEST_WEBHOOK_SECRET, raw_body)

    payment = make_payment(
        status=PaymentStatus.CREATED,
        razorpay_order_id="order_idem001",
    )
    mock_payment_repo.get_by_razorpay_payment_id.return_value = payment

    # First delivery — fresh event
    event = make_webhook_event(razorpay_event_id=event_id, event_type="payment.captured")
    mock_webhook_repo.create_if_not_exists.return_value = (event, True)
    await payment_service.process_webhook(raw_body, sig)

    # Second delivery — duplicate, is_new=False
    mock_webhook_repo.create_if_not_exists.return_value = (event, False)
    await payment_service.process_webhook(raw_body, sig)

    # confirm_order must have been called exactly once despite two deliveries
    assert mock_order_client.confirm_order.await_count == 1, (
        f"Expected confirm_order called once, got {mock_order_client.confirm_order.await_count}"
    )


async def test_duplicate_webhook_mark_processed_called_only_for_new(
    payment_service: PaymentApplicationService,
    mock_payment_repo: AsyncMock,
    mock_webhook_repo: AsyncMock,
    mock_order_client: AsyncMock,
) -> None:
    """mark_processed is called once (for the first delivery); duplicate skips it."""
    event_id = "evt_idem002"
    rz_payment_id = "pay_idem002"
    raw_body = _make_captured_payload(event_id, rz_payment_id)
    sig = sign_webhook(TEST_WEBHOOK_SECRET, raw_body)

    payment = make_payment(status=PaymentStatus.CREATED)
    mock_payment_repo.get_by_razorpay_payment_id.return_value = payment

    event = make_webhook_event(razorpay_event_id=event_id, event_type="payment.captured")

    # First call — new
    mock_webhook_repo.create_if_not_exists.return_value = (event, True)
    await payment_service.process_webhook(raw_body, sig)

    # Second call — duplicate
    mock_webhook_repo.create_if_not_exists.return_value = (event, False)
    await payment_service.process_webhook(raw_body, sig)

    mock_webhook_repo.mark_processed.assert_awaited_once_with(event_id)


async def test_third_delivery_still_ignored(
    payment_service: PaymentApplicationService,
    mock_payment_repo: AsyncMock,
    mock_webhook_repo: AsyncMock,
    mock_order_client: AsyncMock,
) -> None:
    """N deliveries of the same event ID → only one processing, regardless of N."""
    event_id = "evt_idem003"
    rz_payment_id = "pay_idem003"
    raw_body = _make_captured_payload(event_id, rz_payment_id)
    sig = sign_webhook(TEST_WEBHOOK_SECRET, raw_body)

    payment = make_payment(status=PaymentStatus.CREATED)
    mock_payment_repo.get_by_razorpay_payment_id.return_value = payment

    event = make_webhook_event(razorpay_event_id=event_id, event_type="payment.captured")

    # First call processes
    mock_webhook_repo.create_if_not_exists.return_value = (event, True)
    await payment_service.process_webhook(raw_body, sig)

    # Subsequent calls are all duplicates
    mock_webhook_repo.create_if_not_exists.return_value = (event, False)
    for _ in range(4):
        await payment_service.process_webhook(raw_body, sig)

    assert mock_order_client.confirm_order.await_count == 1
    assert mock_webhook_repo.mark_processed.await_count == 1
