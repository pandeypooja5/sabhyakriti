from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from application.dtos.auth_dtos import LoginRequest
from application.services.auth_application_service import AuthApplicationService
from domain.entities.user import User
from domain.value_objects import UserRole

NOW = datetime.now(tz=timezone.utc)


def make_user(**kw) -> User:
    defaults = dict(
        user_id=uuid4(), email="user@example.com", hashed_password=None,
        full_name="Test", role=UserRole.CUSTOMER,
        is_email_verified=True, is_phone_verified=False,
        is_active=True, failed_login_attempts=0, mfa_enabled=False,
        locked_until=None, created_at=NOW, updated_at=NOW,
    )
    defaults.update(kw)
    return User(**defaults)


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
    svc = AuthApplicationService(**defaults)
    svc._jwt.create_access_token.return_value = "access_token"
    svc._jwt.create_refresh_token.return_value = ("refresh_token", str(uuid4()))
    return svc


@pytest.mark.asyncio
async def test_login_success() -> None:
    from application.services.password_hasher import hash_password
    user = make_user(hashed_password=hash_password("correct_pass"))
    svc = make_service()
    svc._users.find_by_email.return_value = user
    svc._users.update.return_value = user
    result = await svc.login_with_email(LoginRequest(email="user@example.com", password="correct_pass"))
    assert hasattr(result, "tokens")


@pytest.mark.asyncio
async def test_login_wrong_password_increments_counter() -> None:
    from application.services.password_hasher import hash_password
    user = make_user(hashed_password=hash_password("correct"))
    svc = make_service()
    svc._users.find_by_email.return_value = user
    svc._users.update.return_value = user
    with pytest.raises(ValueError, match="Invalid"):
        await svc.login_with_email(LoginRequest(email="user@example.com", password="wrong"))
    svc._users.update.assert_called_once()
    assert user.failed_login_attempts == 1


@pytest.mark.asyncio
async def test_login_five_failures_locks_account() -> None:
    from application.services.password_hasher import hash_password
    user = make_user(hashed_password=hash_password("correct"), failed_login_attempts=4)
    svc = make_service()
    svc._users.find_by_email.return_value = user
    svc._users.update.return_value = user
    with pytest.raises(ValueError):
        await svc.login_with_email(LoginRequest(email="user@example.com", password="wrong"))
    assert user.locked_until is not None
    assert user.locked_until > NOW


@pytest.mark.asyncio
async def test_login_locked_account_raises_lookup_error() -> None:
    user = make_user(locked_until=NOW + timedelta(minutes=10))
    svc = make_service()
    svc._users.find_by_email.return_value = user
    with pytest.raises(LookupError, match="locked"):
        await svc.login_with_email(LoginRequest(email="user@example.com", password="any"))


@pytest.mark.asyncio
async def test_login_unverified_email_raises_permission_error() -> None:
    from application.services.password_hasher import hash_password
    user = make_user(hashed_password=hash_password("pass"), is_email_verified=False)
    svc = make_service()
    svc._users.find_by_email.return_value = user
    with pytest.raises(PermissionError, match="verify"):
        await svc.login_with_email(LoginRequest(email="user@example.com", password="pass"))


@pytest.mark.asyncio
async def test_login_nonexistent_email_no_enumeration() -> None:
    svc = make_service()
    svc._users.find_by_email.return_value = None
    with pytest.raises(ValueError, match="Invalid"):
        await svc.login_with_email(LoginRequest(email="nobody@example.com", password="pass"))
