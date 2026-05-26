"""Shared pytest fixtures and factory helpers.

All fixtures in this file are automatically available to all test modules
without explicit import.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from domain.entities.payment import Payment, WebhookEvent
from domain.value_objects import PaymentMethod, PaymentStatus


# ---------------------------------------------------------------------------
# Entity factories
# ---------------------------------------------------------------------------


def make_payment(
    *,
    status: PaymentStatus = PaymentStatus.CREATED,
    method: PaymentMethod = PaymentMethod.RAZORPAY,
    razorpay_order_id: str | None = "order_test123",
    razorpay_payment_id: str | None = None,
    amount: Decimal = Decimal("999.00"),
    attempt_count: int = 1,
    first_attempt_at: datetime | None = None,
    captured_at: datetime | None = None,
    **kwargs: Any,
) -> Payment:
    """Create a Payment domain entity for testing."""
    return Payment(
        payment_id=kwargs.get("payment_id", uuid4()),
        order_id=kwargs.get("order_id", uuid4()),
        user_id=kwargs.get("user_id", uuid4()),
        amount=amount,
        currency="INR",
        method=method,
        status=status,
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        attempt_count=attempt_count,
        first_attempt_at=first_attempt_at or datetime.now(tz=timezone.utc),
        captured_at=captured_at,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )


def make_webhook_event(
    *,
    razorpay_event_id: str = "evt_test123",
    event_type: str = "payment.captured",
    processed: bool = False,
) -> WebhookEvent:
    """Create a WebhookEvent domain entity for testing."""
    return WebhookEvent(
        event_id=uuid4(),
        razorpay_event_id=razorpay_event_id,
        event_type=event_type,
        payload={"event": event_type, "id": razorpay_event_id},
        processed=processed,
    )


def sign_payment(key_secret: str, order_id: str, payment_id: str) -> str:
    """Generate a valid Razorpay payment signature for testing."""
    message = f"{order_id}|{payment_id}".encode()
    return hmac.new(key_secret.encode(), message, hashlib.sha256).hexdigest()


def sign_webhook(webhook_secret: str, body: bytes) -> str:
    """Generate a valid Razorpay webhook signature for testing."""
    return hmac.new(webhook_secret.encode(), body, hashlib.sha256).hexdigest()


# ---------------------------------------------------------------------------
# Mock fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_payment_repo() -> AsyncMock:
    """Mock IPaymentRepository."""
    repo = AsyncMock()
    repo.get_by_order_id = AsyncMock(return_value=None)
    repo.get_by_razorpay_payment_id = AsyncMock(return_value=None)
    repo.create = AsyncMock(side_effect=lambda p: p)
    repo.update = AsyncMock(side_effect=lambda p: p)
    repo.list_stale_created = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_webhook_repo() -> AsyncMock:
    """Mock IWebhookRepository."""
    repo = AsyncMock()
    event = make_webhook_event()
    repo.create_if_not_exists = AsyncMock(return_value=(event, True))
    repo.mark_processed = AsyncMock(return_value=None)
    repo.mark_failed = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_razorpay_adapter() -> AsyncMock:
    """Mock RazorpayAdapter."""
    adapter = AsyncMock()
    adapter.create_order = AsyncMock(
        return_value={"id": "order_rz123", "amount": 99900, "currency": "INR", "status": "created"}
    )
    adapter.create_refund = AsyncMock(
        return_value={"id": "rfnd_test123", "amount": 99900, "status": "processed"}
    )
    return adapter


@pytest.fixture
def mock_order_client() -> AsyncMock:
    """Mock OrderServiceClient."""
    client = AsyncMock()
    client.confirm_order = AsyncMock(return_value=None)
    client.cancel_order = AsyncMock(return_value=None)
    client.get_order_user_id = AsyncMock(return_value=uuid4())
    client.get_order_number = AsyncMock(return_value="ORD-2026-0001")
    return client


@pytest.fixture
def mock_notification_client() -> AsyncMock:
    """Mock NotificationServiceClient."""
    client = AsyncMock()
    client.send_payment_receipt = AsyncMock(return_value=None)
    return client


TEST_KEY_SECRET = "test_key_secret_abc123"
TEST_WEBHOOK_SECRET = "test_webhook_secret_xyz789"
TEST_KEY_ID = "rzp_test_key_id"


@pytest.fixture
def payment_service(
    mock_payment_repo: AsyncMock,
    mock_webhook_repo: AsyncMock,
    mock_razorpay_adapter: AsyncMock,
    mock_order_client: AsyncMock,
    mock_notification_client: AsyncMock,
) -> "PaymentApplicationService":
    """Fully wired PaymentApplicationService with all deps mocked."""
    from application.services.payment_application_service import PaymentApplicationService

    return PaymentApplicationService(
        payment_repo=mock_payment_repo,
        webhook_repo=mock_webhook_repo,
        razorpay_adapter=mock_razorpay_adapter,
        order_client=mock_order_client,
        notification_client=mock_notification_client,
        razorpay_key_id=TEST_KEY_ID,
        razorpay_key_secret=TEST_KEY_SECRET,
        razorpay_webhook_secret=TEST_WEBHOOK_SECRET,
    )
