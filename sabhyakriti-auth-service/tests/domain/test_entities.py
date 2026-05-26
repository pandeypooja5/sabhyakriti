from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from domain.entities.otp_record import OTPRecord
from domain.entities.tokens import EmailVerificationToken, PasswordResetToken, RefreshToken
from domain.entities.user import User
from domain.value_objects import UserRole

NOW = datetime.now(tz=timezone.utc)


def make_user(**kwargs: object) -> User:
    defaults = dict(
        user_id=uuid4(), full_name="Test User", role=UserRole.CUSTOMER,
        is_email_verified=True, is_phone_verified=False, is_active=True,
        failed_login_attempts=0, mfa_enabled=False,
        created_at=NOW, updated_at=NOW, email="test@example.com",
    )
    defaults.update(kwargs)
    return User(**defaults)  # type: ignore[arg-type]


class TestUserLock:
    def test_not_locked_when_locked_until_none(self) -> None:
        user = make_user(locked_until=None)
        assert not user.is_locked(NOW)

    def test_locked_when_locked_until_in_future(self) -> None:
        user = make_user(locked_until=NOW + timedelta(minutes=10))
        assert user.is_locked(NOW)

    def test_not_locked_when_locked_until_in_past(self) -> None:
        user = make_user(locked_until=NOW - timedelta(seconds=1))
        assert not user.is_locked(NOW)

    def test_requires_mfa_only_for_admin_with_mfa_enabled(self) -> None:
        admin = make_user(role=UserRole.ADMIN, mfa_enabled=True)
        customer = make_user(role=UserRole.CUSTOMER, mfa_enabled=True)
        admin_no_mfa = make_user(role=UserRole.ADMIN, mfa_enabled=False)
        assert admin.requires_mfa()
        assert not customer.requires_mfa()
        assert not admin_no_mfa.requires_mfa()


class TestOTPRecord:
    def make_otp(self, **kwargs: object) -> OTPRecord:
        defaults = dict(
            phone_number="9876543210", otp_hash="hash",
            attempt_count=0, last_sent_at=NOW,
            expires_at=NOW + timedelta(minutes=10),
        )
        defaults.update(kwargs)
        return OTPRecord(**defaults)  # type: ignore[arg-type]

    def test_valid_unused_unexpired(self) -> None:
        assert self.make_otp().is_valid(NOW)

    def test_invalid_when_expired(self) -> None:
        otp = self.make_otp(expires_at=NOW - timedelta(seconds=1))
        assert not otp.is_valid(NOW)

    def test_invalid_when_used(self) -> None:
        otp = self.make_otp(used_at=NOW)
        assert not otp.is_valid(NOW)

    def test_invalid_when_max_attempts_reached(self) -> None:
        otp = self.make_otp(attempt_count=3)
        assert not otp.is_valid(NOW)

    @pytest.mark.parametrize("seconds_ago,expected", [(30, True), (61, False)])
    def test_cooldown(self, seconds_ago: int, expected: bool) -> None:
        otp = self.make_otp(last_sent_at=NOW - timedelta(seconds=seconds_ago))
        assert otp.is_send_cooldown_active(NOW) == expected


class TestTokenValidity:
    def test_refresh_token_valid(self) -> None:
        t = RefreshToken(uuid4(), uuid4(), "h", NOW + timedelta(days=30), NOW)
        assert t.is_valid(NOW)

    def test_refresh_token_expired(self) -> None:
        t = RefreshToken(uuid4(), uuid4(), "h", NOW - timedelta(seconds=1), NOW)
        assert not t.is_valid(NOW)

    def test_refresh_token_revoked(self) -> None:
        t = RefreshToken(uuid4(), uuid4(), "h", NOW + timedelta(days=30), NOW, revoked_at=NOW)
        assert not t.is_valid(NOW)

    def test_email_verification_token_valid(self) -> None:
        t = EmailVerificationToken(uuid4(), uuid4(), "h", NOW + timedelta(hours=48), NOW)
        assert t.is_valid(NOW)

    def test_password_reset_token_used(self) -> None:
        t = PasswordResetToken(uuid4(), uuid4(), "h", NOW + timedelta(hours=2), NOW, used_at=NOW)
        assert not t.is_valid(NOW)
