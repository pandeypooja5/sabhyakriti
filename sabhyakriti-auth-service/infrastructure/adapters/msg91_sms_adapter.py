from __future__ import annotations

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

log = structlog.get_logger()

# MSG91 OTP API (v5). We pass our OWN generated OTP via the `otp` param so the
# app keeps generating + verifying the code itself (Redis), and MSG91 only
# delivers the SMS using a DLT-approved template. This route is SMS-only (no
# voice fallback), which fixes the "OTP arrives as a phone call" problem.
_OTP_URL = "https://control.msg91.com/api/v5/otp"


def _is_real_key(value: str) -> bool:
    """True only for a real, non-placeholder MSG91 auth key."""
    return bool(value) and not value.lower().startswith("dummy")


class MSG91SMSAdapter:
    """Implements ISMSAdapter using the MSG91 OTP SMS API.

    Delivery is gated on a real auth key + template id being present — NOT on
    ENVIRONMENT — so the service can keep running in development mode (email
    auto-verify) while still sending real OTP texts. When not configured, the
    OTP is logged instead (local/dev fallback).
    """

    def __init__(self, auth_key: str, template_id: str, sender_id: str = "") -> None:
        self._auth_key = auth_key
        self._template_id = template_id.strip()
        self._sender_id = sender_id.strip()
        self._enabled = _is_real_key(auth_key) and bool(self._template_id)

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=2),
        reraise=True,
    )
    async def send_otp(self, phone_number: str, otp_code: str) -> None:
        if not self._enabled:
            log.info(
                "DEV_OTP (MSG91 not configured)",
                phone_suffix=phone_number[-4:],
                otp_code=otp_code,  # safe to log only when not sending real SMS
            )
            return

        # MSG91 requires the country code. Our stored number is 10 digits.
        digits = phone_number.lstrip("+")
        mobile = digits if digits.startswith("91") and len(digits) > 10 else f"91{digits}"

        params: dict[str, str] = {
            "template_id": self._template_id,
            "mobile": mobile,
            "otp": otp_code,
        }
        if self._sender_id:
            params["sender"] = self._sender_id
        headers = {"authkey": self._auth_key, "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(_OTP_URL, params=params, headers=headers)

        try:
            data = resp.json()
        except ValueError:
            data = {}

        if resp.status_code != 200 or str(data.get("type", "")).lower() != "success":
            log.error(
                "sms_send_failed",
                provider="msg91",
                phone_suffix=phone_number[-4:],
                http_status=resp.status_code,
                details=data.get("message") or resp.text[:200],
            )
            raise RuntimeError(
                f"MSG91 SMS send failed: {data.get('message') or resp.text[:200]}"
            )

        log.info(
            "sms_sent",
            provider="msg91",
            phone_suffix=phone_number[-4:],
            request_id=data.get("message"),
        )
