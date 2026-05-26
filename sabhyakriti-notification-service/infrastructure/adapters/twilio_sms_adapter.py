"""
Twilio SMS adapter (primary SMS provider).

The Twilio Python SDK is synchronous.  The adapter runs it inside
asyncio.get_event_loop().run_in_executor to avoid blocking the event loop.
Tenacity retries up to 2 times on transient errors.
"""

from __future__ import annotations

import asyncio
import functools

import structlog
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client as TwilioClient

logger = structlog.get_logger(__name__)

# Tenacity: up to 2 retries (3 total attempts), exponential backoff 1s/2s
_RETRY = retry(
    retry=retry_if_exception_type(TwilioRestException),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    reraise=True,
)


class TwilioSMSAdapter:
    """Adapter for sending SMS messages via Twilio."""

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str,
    ) -> None:
        self._client = TwilioClient(account_sid, auth_token)
        self._from_number = from_number

    # ── Synchronous inner call (runs in executor) ──────────────────────────────

    @_RETRY  # type: ignore[arg-type]
    def _send_sync(self, to: str, message: str) -> bool:
        """Execute the Twilio messages.create call synchronously with retry."""
        try:
            msg = self._client.messages.create(
                body=message,
                from_=self._from_number,
                to=to,
            )
            logger.info("twilio_send_success", to=to, sid=msg.sid, status=msg.status)
            return True
        except TwilioRestException as exc:
            logger.warning(
                "twilio_send_error",
                to=to,
                status_code=exc.status,
                error_code=exc.code,
                error=str(exc),
            )
            raise

    # ── Public async interface ─────────────────────────────────────────────────

    async def send_sms(self, to: str, message: str) -> bool:
        """
        Send an SMS via Twilio.

        Runs the synchronous Twilio call in the default thread-pool executor.
        Returns True on success, False after all retries are exhausted.
        """
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                None,
                functools.partial(self._send_sync, to=to, message=message),
            )
        except (RetryError, TwilioRestException, Exception) as exc:
            logger.error(
                "twilio_send_failed_after_retries",
                to=to,
                error=str(exc),
            )
            return False
