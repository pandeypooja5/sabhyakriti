from __future__ import annotations

import pyotp


class TOTPService:
    _ISSUER = "Sabhyakriti"
    _VALID_WINDOW = 1  # ±1 window (30s each) for clock drift

    def generate_secret(self) -> str:
        return pyotp.random_base32()

    def get_provisioning_uri(self, secret: str, email: str) -> str:
        return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=self._ISSUER)

    def verify(self, secret: str, code: str) -> bool:
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=self._VALID_WINDOW)
