from __future__ import annotations

import hashlib

import httpx
import structlog

log = structlog.get_logger()

_HIBP_URL = "https://api.pwnedpasswords.com/range/{prefix}"
_TIMEOUT = 2.0


class HIBPAdapter:
    """Implements IHIBPAdapter using the k-anonymity Have I Been Pwned API."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=_TIMEOUT)

    async def is_password_breached(self, password: str) -> bool:
        sha1_hash = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]
        try:
            response = await self._client.get(_HIBP_URL.format(prefix=prefix))
            response.raise_for_status()
        except httpx.TimeoutException:
            log.warning("hibp_timeout", prefix=prefix)
            return False
        except httpx.HTTPError as exc:
            log.warning("hibp_http_error", error=str(exc))
            return False

        for line in response.text.splitlines():
            parts = line.split(":")
            if len(parts) == 2 and parts[0].upper() == suffix:
                count = int(parts[1])
                log.info("hibp_breach_found", count=count)
                return True
        return False

    async def aclose(self) -> None:
        await self._client.aclose()
