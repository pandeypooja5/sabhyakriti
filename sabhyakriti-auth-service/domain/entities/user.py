from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from domain.value_objects import UserRole


@dataclass
class User:
    user_id: UUID
    full_name: str
    role: UserRole
    is_email_verified: bool
    is_phone_verified: bool
    is_active: bool
    failed_login_attempts: int
    mfa_enabled: bool
    created_at: datetime
    updated_at: datetime
    email: str | None = None
    phone_number: str | None = None
    hashed_password: str | None = None
    profile_picture_url: str | None = None
    locked_until: datetime | None = None
    mfa_secret_encrypted: str | None = None

    def is_locked(self, now: datetime) -> bool:
        return self.locked_until is not None and self.locked_until > now

    def requires_mfa(self) -> bool:
        return self.role == UserRole.ADMIN and self.mfa_enabled


@dataclass
class OAuthAccount:
    oauth_id: UUID
    user_id: UUID
    provider: str
    provider_user_id: str
    created_at: datetime
    provider_email: str | None = None
