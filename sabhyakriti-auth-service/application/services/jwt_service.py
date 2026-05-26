from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from jose import JWTError, jwt


class JWTService:
    _ALGORITHM = "RS256"
    _ACCESS_TTL = timedelta(minutes=30)
    _REFRESH_TTL = timedelta(days=30)
    _MFA_PENDING_TTL = timedelta(minutes=5)

    def __init__(self, private_key_pem: str) -> None:
        self._private_key = private_key_pem
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
        key_obj: RSAPrivateKey = load_pem_private_key(private_key_pem.encode(), password=None)  # type: ignore[assignment]
        pub = key_obj.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self._public_key = pub.decode()

    def create_access_token(self, user_id: str, role: str, email: str | None) -> str:
        now = datetime.now(tz=timezone.utc)
        payload: dict[str, Any] = {
            "sub": user_id, "role": role, "email": email,
            "iat": now, "exp": now + self._ACCESS_TTL,
            "jti": str(uuid.uuid4()),
        }
        return jwt.encode(payload, self._private_key, algorithm=self._ALGORITHM)

    def create_refresh_token(self, user_id: str) -> tuple[str, str]:
        """Returns (raw_token, jti)."""
        jti = str(uuid.uuid4())
        now = datetime.now(tz=timezone.utc)
        payload: dict[str, Any] = {
            "sub": user_id, "jti": jti,
            "iat": now, "exp": now + self._REFRESH_TTL,
            "type": "refresh",
        }
        return jwt.encode(payload, self._private_key, algorithm=self._ALGORITHM), jti

    def create_mfa_pending_token(self, user_id: str) -> str:
        now = datetime.now(tz=timezone.utc)
        payload: dict[str, Any] = {
            "sub": user_id, "scope": "mfa_pending",
            "iat": now, "exp": now + self._MFA_PENDING_TTL,
            "jti": str(uuid.uuid4()),
        }
        return jwt.encode(payload, self._private_key, algorithm=self._ALGORITHM)

    def decode_token(self, token: str) -> dict[str, Any]:
        try:
            return jwt.decode(token, self._public_key, algorithms=[self._ALGORITHM])
        except JWTError as exc:
            raise ValueError("Invalid or expired token") from exc

    def get_jwks(self) -> dict[str, Any]:
        """Return public key as JWK Set for /.well-known/jwks.json."""
        from cryptography.hazmat.primitives.serialization import load_pem_public_key
        from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
        import base64
        pub: RSAPublicKey = load_pem_public_key(self._public_key.encode())  # type: ignore[assignment]
        pub_numbers = pub.public_key().public_numbers() if hasattr(pub, "public_key") else pub.public_numbers()  # type: ignore[attr-defined]

        def _b64(n: int) -> str:
            length = (n.bit_length() + 7) // 8
            return base64.urlsafe_b64encode(n.to_bytes(length, "big")).rstrip(b"=").decode()

        return {"keys": [{"kty": "RSA", "use": "sig", "alg": "RS256", "n": _b64(pub_numbers.n), "e": _b64(pub_numbers.e)}]}
