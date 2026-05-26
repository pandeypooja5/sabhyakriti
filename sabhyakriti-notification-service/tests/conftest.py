"""
Pytest fixtures providing fully mocked adapters, repositories, and a wired
NotificationApplicationService for use across all test modules.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape

from application.services.notification_application_service import NotificationApplicationService
from domain.entities.notification_log import NotificationLog
from domain.repositories.i_notification_log_repository import INotificationLogRepository
from domain.value_objects import NotificationChannel, NotificationStatus, NotificationType


# ── Jinja2 environment fixture ─────────────────────────────────────────────────

@pytest.fixture(scope="session")
def jinja_env() -> Environment:
    """Real Jinja2 environment pointing at the actual templates directory."""
    templates_dir = Path(__file__).parent.parent / "templates"
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html"]),
        enable_async=False,
    )


# ── Mock adapters ──────────────────────────────────────────────────────────────

@pytest.fixture
def mock_ses_adapter() -> MagicMock:
    """Mock AWS SES adapter.  send_email returns True by default."""
    adapter = MagicMock()
    adapter.send_email = AsyncMock(return_value=True)
    return adapter


@pytest.fixture
def mock_ses_adapter_failing() -> MagicMock:
    """Mock AWS SES adapter that always returns False (simulates send failure)."""
    adapter = MagicMock()
    adapter.send_email = AsyncMock(return_value=False)
    return adapter


@pytest.fixture
def mock_ses_adapter_raising() -> MagicMock:
    """Mock AWS SES adapter that raises an exception."""
    adapter = MagicMock()
    adapter.send_email = AsyncMock(side_effect=RuntimeError("SES unavailable"))
    return adapter


@pytest.fixture
def mock_twilio_adapter() -> MagicMock:
    """Mock Twilio SMS adapter.  send_sms returns True by default."""
    adapter = MagicMock()
    adapter.send_sms = AsyncMock(return_value=True)
    return adapter


@pytest.fixture
def mock_twilio_adapter_failing() -> MagicMock:
    """Mock Twilio adapter that always returns False."""
    adapter = MagicMock()
    adapter.send_sms = AsyncMock(return_value=False)
    return adapter


@pytest.fixture
def mock_twilio_adapter_raising() -> MagicMock:
    """Mock Twilio adapter that raises an exception."""
    adapter = MagicMock()
    adapter.send_sms = AsyncMock(side_effect=RuntimeError("Twilio unavailable"))
    return adapter


@pytest.fixture
def mock_sns_adapter() -> MagicMock:
    """Mock AWS SNS adapter.  send_sms returns True by default."""
    adapter = MagicMock()
    adapter.send_sms = AsyncMock(return_value=True)
    return adapter


@pytest.fixture
def mock_sns_adapter_failing() -> MagicMock:
    """Mock AWS SNS adapter that always returns False."""
    adapter = MagicMock()
    adapter.send_sms = AsyncMock(return_value=False)
    return adapter


# ── Mock repository ────────────────────────────────────────────────────────────

class InMemoryNotificationLogRepository(INotificationLogRepository):
    """Simple in-memory log repository for tests — stores logs in a list."""

    def __init__(self) -> None:
        self.logs: list[NotificationLog] = []

    async def create(self, log: NotificationLog) -> NotificationLog:
        self.logs.append(log)
        return log


@pytest.fixture
def log_repo() -> InMemoryNotificationLogRepository:
    """Fresh in-memory log repository for each test."""
    return InMemoryNotificationLogRepository()


# ── Wired service fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def notification_service(
    jinja_env: Environment,
    mock_ses_adapter: MagicMock,
    mock_twilio_adapter: MagicMock,
    mock_sns_adapter: MagicMock,
    log_repo: InMemoryNotificationLogRepository,
) -> NotificationApplicationService:
    """Default service: all adapters succeed."""
    return NotificationApplicationService(
        jinja_env=jinja_env,
        ses_adapter=mock_ses_adapter,
        twilio_adapter=mock_twilio_adapter,
        sns_adapter=mock_sns_adapter,
        log_repo=log_repo,
    )


@pytest.fixture
def service_ses_failing(
    jinja_env: Environment,
    mock_ses_adapter_failing: MagicMock,
    mock_twilio_adapter: MagicMock,
    mock_sns_adapter: MagicMock,
    log_repo: InMemoryNotificationLogRepository,
) -> NotificationApplicationService:
    """Service where SES always fails (returns False)."""
    return NotificationApplicationService(
        jinja_env=jinja_env,
        ses_adapter=mock_ses_adapter_failing,
        twilio_adapter=mock_twilio_adapter,
        sns_adapter=mock_sns_adapter,
        log_repo=log_repo,
    )


@pytest.fixture
def service_ses_raising(
    jinja_env: Environment,
    mock_ses_adapter_raising: MagicMock,
    mock_twilio_adapter: MagicMock,
    mock_sns_adapter: MagicMock,
    log_repo: InMemoryNotificationLogRepository,
) -> NotificationApplicationService:
    """Service where SES raises an exception."""
    return NotificationApplicationService(
        jinja_env=jinja_env,
        ses_adapter=mock_ses_adapter_raising,
        twilio_adapter=mock_twilio_adapter,
        sns_adapter=mock_sns_adapter,
        log_repo=log_repo,
    )


@pytest.fixture
def service_twilio_failing_sns_ok(
    jinja_env: Environment,
    mock_ses_adapter: MagicMock,
    mock_twilio_adapter_failing: MagicMock,
    mock_sns_adapter: MagicMock,
    log_repo: InMemoryNotificationLogRepository,
) -> NotificationApplicationService:
    """Service where Twilio fails but SNS succeeds."""
    return NotificationApplicationService(
        jinja_env=jinja_env,
        ses_adapter=mock_ses_adapter,
        twilio_adapter=mock_twilio_adapter_failing,
        sns_adapter=mock_sns_adapter,
        log_repo=log_repo,
    )


@pytest.fixture
def service_twilio_raising_sns_ok(
    jinja_env: Environment,
    mock_ses_adapter: MagicMock,
    mock_twilio_adapter_raising: MagicMock,
    mock_sns_adapter: MagicMock,
    log_repo: InMemoryNotificationLogRepository,
) -> NotificationApplicationService:
    """Service where Twilio raises an exception but SNS succeeds."""
    return NotificationApplicationService(
        jinja_env=jinja_env,
        ses_adapter=mock_ses_adapter,
        twilio_adapter=mock_twilio_adapter_raising,
        sns_adapter=mock_sns_adapter,
        log_repo=log_repo,
    )


@pytest.fixture
def service_all_sms_failing(
    jinja_env: Environment,
    mock_ses_adapter: MagicMock,
    mock_twilio_adapter_raising: MagicMock,
    mock_sns_adapter_failing: MagicMock,
    log_repo: InMemoryNotificationLogRepository,
) -> NotificationApplicationService:
    """Service where both Twilio and SNS fail."""
    return NotificationApplicationService(
        jinja_env=jinja_env,
        ses_adapter=mock_ses_adapter,
        twilio_adapter=mock_twilio_adapter_raising,
        sns_adapter=mock_sns_adapter_failing,
        log_repo=log_repo,
    )


# ── Sample request data ────────────────────────────────────────────────────────

@pytest.fixture
def sample_order_items() -> list[dict]:  # type: ignore[type-arg]
    return [
        {
            "name": "Handwoven Silk Saree",
            "quantity": 1,
            "unit_price": Decimal("4500.00"),
            "total_price": Decimal("4500.00"),
        },
        {
            "name": "Block Print Kurta",
            "quantity": 2,
            "unit_price": Decimal("1200.00"),
            "total_price": Decimal("2400.00"),
        },
    ]
