from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class UserRole(StrEnum):
    CUSTOMER = "CUSTOMER"
    ADMIN = "ADMIN"


class OAuthProvider(StrEnum):
    GOOGLE = "GOOGLE"
    FACEBOOK = "FACEBOOK"


@dataclass(frozen=True)
class IndianPhoneNumber:
    """10-digit Indian mobile number (no country code stored)."""

    number: str

    _PATTERN: re.Pattern[str] = re.compile(r"^[6-9]\d{9}$")

    def __post_init__(self) -> None:
        normalised = re.sub(r"[\s\-]", "", self.number)
        # strip leading +91 or 0 if present
        if normalised.startswith("+91"):
            normalised = normalised[3:]
        elif normalised.startswith("91") and len(normalised) == 12:
            normalised = normalised[2:]
        elif normalised.startswith("0"):
            normalised = normalised[1:]
        object.__setattr__(self, "number", normalised)
        if not self._PATTERN.match(self.number):
            raise ValueError(f"Invalid Indian mobile number: {self.number!r}")

    def __str__(self) -> str:
        return self.number


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 1800  # 30 minutes in seconds
