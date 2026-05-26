from __future__ import annotations

import hashlib
import os as _os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Protocol

import structlog

from application.dtos.auth_dtos import (
    AuthResponse, ChangePasswordRequest, ForgotPasswordRequest,
    LoginRequest, MFAPendingResponse, MFAVerifyRequest, MessageResponse,
    OTPSendRequest, OTPVerifyRequest, RefreshRequest, RegisterRequest,
    ResetPasswordRequest, TokenPairResponse, UpdateProfileRequest,
    UserProfileResponse, VerifyEmailRequest, MFASetupResponse, MFAConfirmSetupRequest,
)
from application.services.aes_encryption_service import AESEncryptionService
from application.services.jwt_service import JWTService
from application.services.password_hasher import hash_password, verify_password
from application.services.totp_service import TOTPService
from domain.entities.otp_record import OTPRecord
from domain.entities.tokens import EmailVerificationToken, PasswordResetToken, RefreshToken
from domain.entities.user import OAuthAccount, User
from domain.repositories.i_otp_repository import IOTPRepository
from domain.repositories.i_token_repository import ITokenRepository
from domain.repositories.i_user_repository import IOAuthAccountRepository, IUserRepository
from domain.repositories.i_verification_repository import (
    IEmailVerificationRepository, IPasswordResetRepository,
)
from domain.value_objects import IndianPhoneNumber, OAuthProvider, TokenPair, UserRole

log = structlog.get_logger()

_MAX_FAILED_ATTEMPTS = 5
_LOCKOUT_MINUTES = 15
_OTP_TTL_MINUTES = 10
_OTP_MAX_ATTEMPTS = 3
_OTP_SEND_COOLDOWN_SECONDS = 60
_OTP_HOURLY_LIMIT = 5
_EMAIL_VERIFY_TTL_HOURS = 48
_PASSWORD_RESET_TTL_HOURS = 2


class IHIBPAdapter(Protocol):
    async def is_password_breached(self, password: str) -> bool: ...


class ISMSAdapter(Protocol):
    async def send_otp(self, phone_number: str, otp_code: str) -> None: ...


class IEmailAdapter(Protocol):
    async def send_verification_email(self, to_email: str, link: str) -> None: ...
    async def send_password_reset_email(self, to_email: str, link: str) -> None: ...


class IOAuthAdapter(Protocol):
    async def exchange_code(self, code: str, redirect_uri: str, code_verifier: str | None) -> dict: ...
    async def get_user_profile(self, access_token: str) -> dict: ...


class IReplayCache(Protocol):
    async def is_used(self, key: str) -> bool: ...
    async def mark_used(self, key: str, ttl_seconds: int) -> None: ...


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _to_profile(user: User) -> UserProfileResponse:
    return UserProfileResponse(
        user_id=user.user_id,
        email=user.email,
        phone_number=user.phone_number,
        full_name=user.full_name,
        role=user.role,
        is_email_verified=user.is_email_verified,
        profile_picture_url=user.profile_picture_url,
        mfa_enabled=user.mfa_enabled,
    )


class AuthApplicationService:
    def __init__(
        self,
        user_repo: IUserRepository,
        oauth_repo: IOAuthAccountRepository,
        token_repo: ITokenRepository,
        otp_repo: IOTPRepository,
        email_verify_repo: IEmailVerificationRepository,
        password_reset_repo: IPasswordResetRepository,
        jwt_service: JWTService,
        aes_service: AESEncryptionService,
        totp_service: TOTPService,
        hibp_adapter: IHIBPAdapter,
        sms_adapter: ISMSAdapter,
        email_adapter: IEmailAdapter,
        replay_cache: IReplayCache,
        frontend_origin: str,
    ) -> None:
        self._users = user_repo
        self._oauth = oauth_repo
        self._tokens = token_repo
        self._otp = otp_repo
        self._email_verify = email_verify_repo
        self._password_reset = password_reset_repo
        self._jwt = jwt_service
        self._aes = aes_service
        self._totp = totp_service
        self._hibp = hibp_adapter
        self._sms = sms_adapter
        self._email = email_adapter
        self._replay = replay_cache
        self._frontend_origin = frontend_origin
        self._dev_mode = _os.getenv("ENVIRONMENT", "development").lower() == "development"

    # ── helpers ──────────────────────────────────────────────────────────────

    async def _issue_token_pair(self, user: User) -> TokenPairResponse:
        access = self._jwt.create_access_token(
            str(user.user_id), user.role, user.email
        )
        raw_refresh, jti = self._jwt.create_refresh_token(str(user.user_id))
        now = datetime.now(tz=timezone.utc)
        rt = RefreshToken(
            token_id=uuid.UUID(jti),
            user_id=user.user_id,
            token_hash=_sha256(raw_refresh),
            expires_at=now + timedelta(days=30),
            created_at=now,
        )
        await self._tokens.store(rt)
        return TokenPairResponse(access_token=access, refresh_token=raw_refresh)

    # ── flows ─────────────────────────────────────────────────────────────────

    async def register_with_email(self, req: RegisterRequest) -> MessageResponse:
        email = req.email.lower()
        if await self._users.find_by_email(email):
            raise ValueError("An account with this email already exists.")
        if await self._hibp.is_password_breached(req.password):
            raise ValueError("This password has appeared in a data breach. Please choose a different one.")
        now = datetime.now(tz=timezone.utc)
        user = User(
            user_id=uuid.uuid4(), email=email,
            hashed_password=hash_password(req.password),
            full_name=req.full_name.strip(), role=UserRole.CUSTOMER,
            is_email_verified=False, is_phone_verified=False, is_active=True,
            failed_login_attempts=0, mfa_enabled=False,
            created_at=now, updated_at=now,
        )
        # In dev mode, auto-verify email so users can log in immediately
        if self._dev_mode:
            user.is_email_verified = True
        user = await self._users.create(user)

        if self._dev_mode:
            log.info(
                "DEV_MODE: user auto-verified, no email sent",
                email=email,
            )
            tokens = await self._issue_token_pair(user)
            return AuthResponse(tokens=tokens, user=_to_profile(user))

        raw_token = secrets.token_urlsafe(32)
        ev = EmailVerificationToken(
            token_id=uuid.uuid4(), user_id=user.user_id,
            token_hash=_sha256(raw_token),
            expires_at=now + timedelta(hours=_EMAIL_VERIFY_TTL_HOURS),
            created_at=now,
        )
        await self._email_verify.create(ev)
        link = f"{self._frontend_origin}/verify-email?token={raw_token}"
        await self._email.send_verification_email(email, link)
        log.info("user_registered", email_domain=email.split("@")[-1])
        return MessageResponse(message="Registration successful. Please verify your email.")

    async def verify_email(self, req: VerifyEmailRequest) -> AuthResponse:
        now = datetime.now(tz=timezone.utc)
        token_hash = _sha256(req.token)
        ev = await self._email_verify.find_by_hash(token_hash)
        if not ev or not ev.is_valid(now):
            raise ValueError("Invalid or expired verification link.")
        user = await self._users.find_by_id(ev.user_id)
        if not user:
            raise ValueError("User not found.")
        user.is_email_verified = True
        user.updated_at = now
        user = await self._users.update(user)
        await self._email_verify.mark_used(ev.token_id)
        tokens = await self._issue_token_pair(user)
        return AuthResponse(tokens=tokens, user=_to_profile(user))

    async def login_with_email(self, req: LoginRequest) -> AuthResponse | MFAPendingResponse:
        now = datetime.now(tz=timezone.utc)
        email = req.email.lower()
        user = await self._users.find_by_email(email)
        if not user:
            raise ValueError("Invalid email or password.")
        if not user.is_active:
            raise PermissionError("Account suspended. Contact support.")
        if user.is_locked(now):
            remaining = int((user.locked_until - now).total_seconds())  # type: ignore[operator]
            raise LookupError(f"Account temporarily locked. Try again in {remaining // 60 + 1} minutes.")
        if not user.is_email_verified:
            raise PermissionError("Please verify your email before logging in.")
        if not user.hashed_password or not verify_password(req.password, user.hashed_password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= _MAX_FAILED_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=_LOCKOUT_MINUTES)
                log.warning("account_locked", user_id=str(user.user_id))
            user.updated_at = now
            await self._users.update(user)
            raise ValueError("Invalid email or password.")
        user.failed_login_attempts = 0
        user.locked_until = None
        user.updated_at = now
        user = await self._users.update(user)
        if user.requires_mfa():
            mfa_token = self._jwt.create_mfa_pending_token(str(user.user_id))
            return MFAPendingResponse(mfa_token=mfa_token)
        tokens = await self._issue_token_pair(user)
        return AuthResponse(tokens=tokens, user=_to_profile(user))

    async def login_with_oauth(
        self,
        provider: str,
        code: str,
        redirect_uri: str,
        adapter: IOAuthAdapter,
        code_verifier: str | None = None,
    ) -> AuthResponse:
        now = datetime.now(tz=timezone.utc)
        token_data = await adapter.exchange_code(code, redirect_uri, code_verifier)
        profile = await adapter.get_user_profile(token_data["access_token"])
        provider_user_id: str = profile["id"] if provider == OAuthProvider.FACEBOOK else profile["sub"]
        provider_email: str | None = profile.get("email")
        oauth_account = await self._oauth.find_by_provider(provider, provider_user_id)
        is_new = False
        if oauth_account:
            user = await self._users.find_by_id(oauth_account.user_id)
            if not user:
                raise RuntimeError("Linked user not found.")
        else:
            user = await self._users.find_by_email(provider_email.lower()) if provider_email else None
            if user:
                # auto-link
                oa = OAuthAccount(
                    oauth_id=uuid.uuid4(), user_id=user.user_id,
                    provider=provider, provider_user_id=provider_user_id,
                    provider_email=provider_email, created_at=now,
                )
                await self._oauth.create(oa)
            else:
                is_new = True
                user = User(
                    user_id=uuid.uuid4(), email=provider_email,
                    full_name=profile.get("name", ""),
                    profile_picture_url=profile.get("picture"),
                    hashed_password=None, role=UserRole.CUSTOMER,
                    is_email_verified=True, is_phone_verified=False, is_active=True,
                    failed_login_attempts=0, mfa_enabled=False,
                    created_at=now, updated_at=now,
                )
                user = await self._users.create(user)
                oa = OAuthAccount(
                    oauth_id=uuid.uuid4(), user_id=user.user_id,
                    provider=provider, provider_user_id=provider_user_id,
                    provider_email=provider_email, created_at=now,
                )
                await self._oauth.create(oa)
        if not user.is_active:
            raise PermissionError("Account suspended.")
        tokens = await self._issue_token_pair(user)
        return AuthResponse(tokens=tokens, user=_to_profile(user), is_new_user=is_new)

    async def send_otp(self, req: OTPSendRequest) -> MessageResponse:
        phone = str(IndianPhoneNumber(req.phone_number))
        now = datetime.now(tz=timezone.utc)
        existing = await self._otp.find_by_phone(phone)
        if existing and existing.is_send_cooldown_active(now):
            raise ValueError("Please wait 1 minute before requesting a new OTP.")
        otp_code = f"{secrets.randbelow(1_000_000):06d}"
        record = OTPRecord(
            phone_number=phone, otp_hash=hash_password(otp_code),
            attempt_count=0, last_sent_at=now,
            expires_at=now + timedelta(minutes=_OTP_TTL_MINUTES),
        )
        await self._otp.upsert(record)
        await self._sms.send_otp(phone, otp_code)
        log.info("otp_sent", phone_suffix=phone[-4:])
        return MessageResponse(message="OTP sent.", **{"expires_in": _OTP_TTL_MINUTES * 60})  # type: ignore[arg-type]

    async def verify_otp(self, req: OTPVerifyRequest) -> AuthResponse:
        phone = str(IndianPhoneNumber(req.phone_number))
        now = datetime.now(tz=timezone.utc)
        record = await self._otp.find_by_phone(phone)
        if not record:
            raise ValueError("No OTP found for this number.")
        if not record.is_valid(now):
            raise ValueError("OTP has expired or is no longer valid. Please request a new one.")
        if not verify_password(req.otp_code, record.otp_hash):
            new_count = await self._otp.increment_attempts(phone)
            if new_count >= _OTP_MAX_ATTEMPTS:
                await self._otp.invalidate(phone)
            raise ValueError("Invalid OTP.")
        await self._otp.invalidate(phone)
        user = await self._users.find_by_phone(phone)
        is_new = False
        if not user:
            is_new = True
            user = User(
                user_id=uuid.uuid4(), phone_number=phone,
                full_name="", hashed_password=None, role=UserRole.CUSTOMER,
                is_email_verified=False, is_phone_verified=True, is_active=True,
                failed_login_attempts=0, mfa_enabled=False,
                created_at=now, updated_at=now,
            )
            user = await self._users.create(user)
        else:
            user.is_phone_verified = True
            user.updated_at = now
            user = await self._users.update(user)
        tokens = await self._issue_token_pair(user)
        return AuthResponse(tokens=tokens, user=_to_profile(user), is_new_user=is_new)

    async def refresh_tokens(self, req: RefreshRequest) -> TokenPairResponse:
        now = datetime.now(tz=timezone.utc)
        token_hash = _sha256(req.refresh_token)
        stored = await self._tokens.find_by_hash(token_hash)
        if not stored or not stored.is_valid(now):
            raise ValueError("Invalid or expired refresh token.")
        claims = self._jwt.decode_token(req.refresh_token)
        if claims.get("type") != "refresh":
            raise ValueError("Invalid token type.")
        await self._tokens.revoke(stored.token_id)
        user = await self._users.find_by_id(stored.user_id)
        if not user or not user.is_active:
            raise PermissionError("Account unavailable.")
        return await self._issue_token_pair(user)

    async def logout(self, refresh_token: str) -> MessageResponse:
        token_hash = _sha256(refresh_token)
        stored = await self._tokens.find_by_hash(token_hash)
        if stored:
            await self._tokens.revoke(stored.token_id)
        return MessageResponse(message="Logged out successfully.")

    async def logout_all(self, user_id: uuid.UUID) -> MessageResponse:
        await self._tokens.revoke_all_for_user(user_id)
        return MessageResponse(message="Logged out from all devices.")

    async def verify_mfa(self, req: MFAVerifyRequest) -> AuthResponse:
        claims = self._jwt.decode_token(req.mfa_token)
        if claims.get("scope") != "mfa_pending":
            raise ValueError("Invalid MFA token.")
        user_id = uuid.UUID(claims["sub"])
        user = await self._users.find_by_id(user_id)
        if not user or not user.mfa_enabled or not user.mfa_secret_encrypted:
            raise ValueError("MFA not configured.")
        secret = self._aes.decrypt(user.mfa_secret_encrypted)
        replay_key = f"mfa_used:{user_id}:{req.totp_code}"
        if await self._replay.is_used(replay_key):
            raise ValueError("TOTP code already used.")
        if not self._totp.verify(secret, req.totp_code):
            raise ValueError("Invalid TOTP code.")
        await self._replay.mark_used(replay_key, ttl_seconds=90)
        tokens = await self._issue_token_pair(user)
        return AuthResponse(tokens=tokens, user=_to_profile(user))

    async def setup_mfa(self, user_id: uuid.UUID) -> MFASetupResponse:
        user = await self._users.find_by_id(user_id)
        if not user or user.role != UserRole.ADMIN:
            raise PermissionError("MFA setup is only available for admin accounts.")
        secret = self._totp.generate_secret()
        uri = self._totp.get_provisioning_uri(secret, user.email or str(user_id))
        # Store temporarily encrypted; confirmed in confirm_mfa_setup
        user.mfa_secret_encrypted = self._aes.encrypt(secret)
        user.updated_at = datetime.now(tz=timezone.utc)
        await self._users.update(user)
        return MFASetupResponse(secret=secret, provisioning_uri=uri)

    async def confirm_mfa_setup(self, user_id: uuid.UUID, req: MFAConfirmSetupRequest) -> MessageResponse:
        user = await self._users.find_by_id(user_id)
        if not user or not user.mfa_secret_encrypted:
            raise ValueError("MFA setup not initiated.")
        secret = self._aes.decrypt(user.mfa_secret_encrypted)
        if not self._totp.verify(secret, req.totp_code):
            raise ValueError("Invalid TOTP code. Please try again.")
        user.mfa_enabled = True
        user.updated_at = datetime.now(tz=timezone.utc)
        await self._users.update(user)
        return MessageResponse(message="MFA enabled successfully.")

    async def change_password(self, user_id: uuid.UUID, req: ChangePasswordRequest) -> MessageResponse:
        user = await self._users.find_by_id(user_id)
        if not user or not user.hashed_password:
            raise ValueError("Cannot change password for this account.")
        if not verify_password(req.current_password, user.hashed_password):
            raise ValueError("Current password is incorrect.")
        if req.current_password == req.new_password:
            raise ValueError("New password must differ from current password.")
        if await self._hibp.is_password_breached(req.new_password):
            raise ValueError("This password has appeared in a data breach.")
        user.hashed_password = hash_password(req.new_password)
        user.updated_at = datetime.now(tz=timezone.utc)
        await self._users.update(user)
        await self._tokens.revoke_all_for_user(user_id)
        return MessageResponse(message="Password changed. Please log in again.")

    async def forgot_password(self, req: ForgotPasswordRequest) -> MessageResponse:
        email = req.email.lower()
        user = await self._users.find_by_email(email)
        if user and user.is_active:
            now = datetime.now(tz=timezone.utc)
            await self._password_reset.invalidate_existing_for_user(user.user_id)
            raw_token = secrets.token_urlsafe(32)
            pr = PasswordResetToken(
                token_id=uuid.uuid4(), user_id=user.user_id,
                token_hash=_sha256(raw_token),
                expires_at=now + timedelta(hours=_PASSWORD_RESET_TTL_HOURS),
                created_at=now,
            )
            await self._password_reset.create(pr)
            link = f"{self._frontend_origin}/reset-password?token={raw_token}"
            await self._email.send_password_reset_email(email, link)
        return MessageResponse(message="If that email is registered, you will receive a reset link.")

    async def reset_password(self, req: ResetPasswordRequest) -> MessageResponse:
        now = datetime.now(tz=timezone.utc)
        token_hash = _sha256(req.token)
        pr = await self._password_reset.find_by_hash(token_hash)
        if not pr or not pr.is_valid(now):
            raise ValueError("Invalid or expired reset link.")
        if await self._hibp.is_password_breached(req.new_password):
            raise ValueError("This password has appeared in a data breach.")
        user = await self._users.find_by_id(pr.user_id)
        if not user:
            raise ValueError("User not found.")
        user.hashed_password = hash_password(req.new_password)
        user.failed_login_attempts = 0
        user.locked_until = None
        user.updated_at = now
        await self._users.update(user)
        await self._password_reset.mark_used(pr.token_id)
        await self._tokens.revoke_all_for_user(user.user_id)
        return MessageResponse(message="Password reset successful. Please log in.")

    async def update_profile(self, user_id: uuid.UUID, req: UpdateProfileRequest) -> UserProfileResponse:
        user = await self._users.find_by_id(user_id)
        if not user:
            raise ValueError("User not found.")
        if req.full_name is not None:
            user.full_name = req.full_name.strip()
        if req.profile_picture_url is not None:
            user.profile_picture_url = req.profile_picture_url
        user.updated_at = datetime.now(tz=timezone.utc)
        user = await self._users.update(user)
        return _to_profile(user)
