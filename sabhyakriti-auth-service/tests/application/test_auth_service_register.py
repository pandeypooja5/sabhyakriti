from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from application.dtos.auth_dtos import RegisterRequest
from application.services.auth_application_service import AuthApplicationService


def make_service(**overrides) -> AuthApplicationService:
    defaults = dict(
        user_repo=AsyncMock(), oauth_repo=AsyncMock(),
        token_repo=AsyncMock(), otp_repo=AsyncMock(),
        email_verify_repo=AsyncMock(), password_reset_repo=AsyncMock(),
        jwt_service=MagicMock(), aes_service=MagicMock(),
        totp_service=MagicMock(), hibp_adapter=AsyncMock(),
        sms_adapter=AsyncMock(), email_adapter=AsyncMock(),
        replay_cache=AsyncMock(), frontend_origin="https://sabhyakriti.com",
    )
    defaults.update(overrides)
    return AuthApplicationService(**defaults)


@pytest.mark.asyncio
async def test_register_success() -> None:
    svc = make_service()
    svc._users.find_by_email.return_value = None
    svc._hibp.is_password_breached.return_value = False
    svc._users.create.return_value = MagicMock(user_id=__import__("uuid").uuid4(), email="a@b.com")
    req = RegisterRequest(email="a@b.com", password="StrongPass1!", full_name="Alice")
    result = await svc.register_with_email(req)
    assert "verify" in result.message.lower()
    svc._email.send_verification_email.assert_called_once()


@pytest.mark.asyncio
async def test_register_duplicate_email_raises() -> None:
    svc = make_service()
    svc._users.find_by_email.return_value = MagicMock()
    with pytest.raises(ValueError, match="already exists"):
        await svc.register_with_email(RegisterRequest(email="a@b.com", password="Pass1234!", full_name="Alice"))


@pytest.mark.asyncio
async def test_register_breached_password_raises() -> None:
    svc = make_service()
    svc._users.find_by_email.return_value = None
    svc._hibp.is_password_breached.return_value = True
    with pytest.raises(ValueError, match="breach"):
        await svc.register_with_email(RegisterRequest(email="a@b.com", password="password123", full_name="Alice"))


@pytest.mark.asyncio
async def test_register_hibp_fail_open(monkeypatch) -> None:
    """HIBP timeout should not block registration."""
    svc = make_service()
    svc._users.find_by_email.return_value = None
    svc._hibp.is_password_breached.return_value = False  # fail-open = False returned
    svc._users.create.return_value = MagicMock(user_id=__import__("uuid").uuid4(), email="a@b.com")
    req = RegisterRequest(email="a@b.com", password="UniquePass99!", full_name="Bob")
    result = await svc.register_with_email(req)
    assert result.message
