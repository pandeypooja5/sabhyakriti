"""
AWS SES email adapter.

Uses boto3 (synchronous) run inside asyncio.get_event_loop().run_in_executor
so it does not block the event loop.  Tenacity retries the call up to 2 times
on transient errors before marking the attempt as failed.
"""

from __future__ import annotations

import asyncio
import functools
from typing import Any

import boto3
import structlog
from botocore.exceptions import BotoCoreError, ClientError
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = structlog.get_logger(__name__)

# Tenacity: up to 2 retries (3 total attempts), exponential backoff 1s/2s
_RETRY = retry(
    retry=retry_if_exception_type((BotoCoreError, ClientError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    reraise=True,
)


class AWSSESAdapter:
    """Adapter for sending transactional emails via AWS Simple Email Service."""

    def __init__(
        self,
        region: str,
        from_email: str,
        from_name: str,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
    ) -> None:
        self._from_address = f'"{from_name}" <{from_email}>'
        self._client: Any = boto3.client(
            "ses",
            region_name=region,
            **(
                {
                    "aws_access_key_id": aws_access_key_id,
                    "aws_secret_access_key": aws_secret_access_key,
                }
                if aws_access_key_id
                else {}
            ),
        )

    # ── Internal synchronous call (run inside executor) ────────────────────────

    @_RETRY  # type: ignore[arg-type]
    def _send_sync(
        self,
        to: str,
        from_email: str | None,
        subject: str,
        html_body: str,
    ) -> bool:
        """Execute the SES send_email API call synchronously with retry."""
        source = from_email if from_email else self._from_address
        try:
            response = self._client.send_email(
                Source=source,
                Destination={"ToAddresses": [to]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {
                        "Html": {"Data": html_body, "Charset": "UTF-8"},
                    },
                },
            )
            message_id = response.get("MessageId", "unknown")
            logger.info("ses_send_success", to=to, message_id=message_id)
            return True
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "Unknown")
            logger.warning("ses_client_error", to=to, error_code=error_code, error=str(exc))
            raise

    # ── Public async interface ─────────────────────────────────────────────────

    async def send_email(
        self,
        to: str,
        from_email: str | None,
        subject: str,
        html_body: str,
    ) -> bool:
        """
        Send an email via SES.

        Runs the synchronous boto3 call in the default thread-pool executor so
        it does not block the event loop.  Returns True on success, False on
        final failure after retries.
        """
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                None,
                functools.partial(
                    self._send_sync,
                    to=to,
                    from_email=from_email,
                    subject=subject,
                    html_body=html_body,
                ),
            )
        except (RetryError, BotoCoreError, ClientError, Exception) as exc:
            logger.error(
                "ses_send_failed_after_retries",
                to=to,
                subject=subject,
                error=str(exc),
            )
            return False
