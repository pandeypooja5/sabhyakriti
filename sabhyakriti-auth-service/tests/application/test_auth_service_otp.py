from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from application.dtos.auth_dtos import OTPSendRequest, OTPVerifyRequest
from application.services.auth_application_service import AuthApplicationService
from application.services.password_hasher import hash_password
from domain.entities.otp_record import OTPRecord

NOW = datetime.now(tz=timezone.utc)


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
    svc._jwt.create_access_token.return_value = "access"
    svc._jwt.create_refresh_token.return_value = ("refresh", str(uuid4()))
    return svc


@pytest.mark.asyncio
async def test_send_otp_success() -> None:
    svc = make_service()
    svc._otp.find_by_phone.return_value = None
    req = OTPSendRequest(phone_number="9876543210")
    result = await svc.send_otp(req)
    svc._sms.send_otp.assert_called_once()
    assert "OTP" in result.message


@pytest.mark.asyncio
async def test_send_otp_cooldown_enforced() -> None:
    svc = make_service()
    recent_otp = OTPRecord(
        phone_number="9876543210", otp_hash="hash", attempt_count=0,
        last_sent_at=NOW - timedelta(seconds=30),  # only 30s ago
        expires_at=NOW + timedelta(minutes=10),
    )
    svc._otp.find_by_phone.return_value = recent_otp
    with pytest.raises(ValueError, match="wait"):
        await svc.send_otp(OTPSendRequest(phone_number="9876543210"))


@pytest.mark.asyncio
async def test_verify_otp_success_new_user() -> None:
    otp_code = "123456"
    otp = OTPRecord(
        phone_number="9876543210", otp_hash=hash_password(otp_code),
        attempt_count=0, last_sent_at=NOW,
        expires_at=NOW + timedelta(minutes=10),
    )
    svc = make_service()
    svc._otp.find_by_phone.return_value = otp
    svc._users.find_by_phone.return_value = None
    new_user = MagicMock(user_id=uuid4(), email=None, phone_number="9876543210",
                         full_name="", role="CUSTOMER", is_email_verified=False,
                         profile_picture_url=None, mfa_enabled=False)
    svc._users.create.return_value = new_user
    result = await svc.verify_otp(OTPVerifyRequest(phone_number="9876543210", otp_code=otp_code))
    assert result.is_new_user is True


@pytest.mark.asyncio
async def test_verify_otp_wrong_code_increments_attempts() -> None:
    otp = OTPRecord(
        phone_number="9876543210", otp_hash=hash_password("654321"),
        attempt_count=0, last_sent_at=NOW,
        expires_at=NOW + timedelta(minutes=10),
    )
    svc = make_service()
    svc._otp.find_by_phone.return_value = otp
    svc._otp.increment_attempts.return_value = 1
    with pytest.raises(ValueError, match="Invalid OTP"):
        await svc.verify_otp(OTPVerifyRequest(phone_number="9876543210", otp_code="000000"))
    svc._otp.increment_attempts.assert_called_once()


@pytest.mark.asyncio
async def test_verify_otp_expired_raises() -> None:
    otp = OTPRecord(
        phone_number="9876543210", otp_hash="hash",
        attempt_count=0, last_sent_at=NOW,
        expires_at=NOW - timedelta(seconds=1),
    )
    svc = make_service()
    svc._otp.find_by_phone.return_value = otp
    with pytest.raises(ValueError, match="expired"):
        await svc.verify_otp(OTPVerifyRequest(phone_number="9876543210", otp_code="123456"))
