from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class AESEncryptionService:
    """AES-256-GCM for encrypting TOTP secrets at rest."""

    def __init__(self, key_b64: str) -> None:
        self._key = base64.b64decode(key_b64)
        if len(self._key) != 32:
            raise ValueError("AES key must be 32 bytes (256-bit)")

    def encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(12)
        aesgcm = AESGCM(self._key)
        ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
        return base64.b64encode(nonce + ct).decode()

    def decrypt(self, ciphertext_b64: str) -> str:
        data = base64.b64decode(ciphertext_b64)
        nonce, ct = data[:12], data[12:]
        aesgcm = AESGCM(self._key)
        return aesgcm.decrypt(nonce, ct, None).decode()
