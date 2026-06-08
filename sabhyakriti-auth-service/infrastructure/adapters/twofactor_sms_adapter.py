from __future__ import annotations

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

log = structlog.get_logger()

_BASE_URL = "https://2factor.in/API/V1"


def _is_real_key(api_key: str) -> bool:
    """True only for a real, non-placeholder 2Factor API key."""
    return bool(api_key) and not api_key.lower().startswith("dummy")


class TwoFactorSMSAdapter:
    """Implements ISMSAdapter using the 2Factor.in SMS OTP API.

    Unlike the Twilio adapter, delivery is gated on the presence of a real
    API key — NOT on ENVIRONMENT. This lets the rest of the service keep
    running in ``ENVIRONMENT=development`` (e.g. email auto-verify) while
    still sending real OTP texts as soon as a valid key is configured.

    The application generates and verifies the OTP itself, so we use the
    2Factor "custom OTP value" endpoint to deliver our own code via a
    DLT-approved template:

        GET {base}/{api_key}/SMS/{phone}/{otp}/{template_name}

    When no real key is set, the OTP is logged instead (local/dev fallback).
    """

    def __init__(self, api_key: str, template_name: str = "") -> None:
        self._api_key = api_key
        self._template_name = template_name.strip()
        self._enabled = _is_real_key(api_key)

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=2),
        reraise=True,
    )
    async def send_otp(self, phone_number: str, otp_code: str) -> None:
        if not self._enabled:
            # No real provider configured — log instead of sending.
            log.info(
                "DEV_OTP (2Factor not configured)",
                phone_suffix=phone_number[-4:],
                otp_code=otp_code,  # safe to log only when not sending real SMS
            )
            return

        # 2Factor accepts a bare 10-digit Indian number or +91 prefixed.
        url = f"{_BASE_URL}/{self._api_key}/SMS/{phone_number}/{otp_code}"
        if self._template_name:
            url += f"/{self._template_name}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)

        try:
            data = resp.json()
        except ValueError:
            data = {}

        status = str(data.get("Status", "")).lower()
        if resp.status_code != 200 or status != "success":
            # Don't leak the API key (it's in the URL) — log details only.
            log.error(
                "sms_send_failed",
                provider="2factor",
                phone_suffix=phone_number[-4:],
                http_status=resp.status_code,
                details=data.get("Details"),
            )
            raise RuntimeError(
                f"2Factor SMS send failed: {data.get('Details') or resp.text[:200]}"
            )

        log.info(
            "sms_sent",
            provider="2factor",
            phone_suffix=phone_number[-4:],
            session_id=data.get("Details"),
        )
