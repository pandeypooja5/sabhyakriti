from __future__ import annotations

import asyncio
import os

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

log = structlog.get_logger()
_IS_DEV = os.getenv("ENVIRONMENT", "development").lower() == "development"


class TwilioSMSAdapter:
    """Implements ISMSAdapter using the Twilio REST API.

    In ENVIRONMENT=development, OTP codes are printed to auth-service logs
    instead of being sent via Twilio — no credentials required locally.
    """

    def __init__(self, account_sid: str, auth_token: str, from_number: str) -> None:
        self._from_number = from_number
        if _IS_DEV:
            self._client = None
        else:
            from twilio.rest import Client  # import only when needed
            self._client = Client(account_sid, auth_token)

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=2), reraise=False)
    async def send_otp(self, phone_number: str, otp_code: str) -> None:
        if _IS_DEV or self._client is None:
            # Dev mode — OTP visible in auth-service container logs
            log.info(
                "DEV_OTP (not sent via Twilio)",
                phone_suffix=phone_number[-4:],
                otp_code=otp_code,  # safe to log in dev only
            )
            return
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self._client.messages.create(  # type: ignore[union-attr]
                body=f"Your Sabhyakriti OTP is {otp_code}. Valid for 10 minutes. Do not share it.",
                from_=self._from_number,
                to=f"+91{phone_number}",
            ),
        )
        log.info("sms_sent", phone_suffix=phone_number[-4:])
