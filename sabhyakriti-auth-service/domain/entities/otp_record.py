from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class OTPRecord:
    phone_number: str
    otp_hash: str
    attempt_count: int
    last_sent_at: datetime
    expires_at: datetime
    used_at: datetime | None = None

    def is_valid(self, now: datetime) -> bool:
        return self.used_at is None and self.expires_at > now and self.attempt_count < 3

    def is_send_cooldown_active(self, now: datetime, cooldown_seconds: int = 60) -> bool:
        return (now - self.last_sent_at).total_seconds() < cooldown_seconds
