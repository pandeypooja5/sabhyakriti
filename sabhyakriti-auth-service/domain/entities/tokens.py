from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class RefreshToken:
    token_id: UUID
    user_id: UUID
    token_hash: str
    expires_at: datetime
    created_at: datetime
    device_hint: str | None = None
    revoked_at: datetime | None = None

    def is_valid(self, now: datetime) -> bool:
        return self.revoked_at is None and self.expires_at > now


@dataclass
class EmailVerificationToken:
    token_id: UUID
    user_id: UUID
    token_hash: str
    expires_at: datetime
    created_at: datetime
    used_at: datetime | None = None

    def is_valid(self, now: datetime) -> bool:
        return self.used_at is None and self.expires_at > now


@dataclass
class PasswordResetToken:
    token_id: UUID
    user_id: UUID
    token_hash: str
    expires_at: datetime
    created_at: datetime
    used_at: datetime | None = None

    def is_valid(self, now: datetime) -> bool:
        return self.used_at is None and self.expires_at > now
