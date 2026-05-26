"""
AWS SNS SMS adapter (fallback SMS provider).

Used automatically by NotificationApplicationService when Twilio fails.
Uses boto3 SNS publish run inside an executor to remain non-blocking.
No tenacity retry here — this is already the fallback path.
"""

from __future__ import annotations

import asyncio
import functools
from typing import Any

import boto3
import structlog
from botocore.exceptions import BotoCoreError, ClientError

logger = structlog.get_logger(__name__)


class AWSSNSAdapter:
    """Adapter for sending SMS messages via AWS SNS as a fallback provider."""

    def __init__(
        self,
        region: str,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
    ) -> None:
        self._client: Any = boto3.client(
            "sns",
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

    # ── Synchronous inner call (runs in executor) ──────────────────────────────

    def _publish_sync(self, to: str, message: str) -> bool:
        """Execute the SNS publish call synchronously."""
        try:
            response = self._client.publish(
                PhoneNumber=to,
                Message=message,
                MessageAttributes={
                    "AWS.SNS.SMS.SMSType": {
                        "DataType": "String",
                        "StringValue": "Transactional",
                    },
                    "AWS.SNS.SMS.SenderID": {
                        "DataType": "String",
                        "StringValue": "Sabhyakrti",  # max 11 chars for sender ID
                    },
                },
            )
            message_id = response.get("MessageId", "unknown")
            logger.info("sns_sms_send_success", to=to, message_id=message_id)
            return True
        except (BotoCoreError, ClientError) as exc:
            logger.error("sns_sms_send_error", to=to, error=str(exc))
            raise

    # ── Public async interface ─────────────────────────────────────────────────

    async def send_sms(self, to: str, message: str) -> bool:
        """
        Send an SMS via AWS SNS.

        Runs the synchronous boto3 call in the default thread-pool executor.
        Returns True on success, False on failure.
        """
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                None,
                functools.partial(self._publish_sync, to=to, message=message),
            )
        except Exception as exc:
            logger.error(
                "sns_sms_adapter_failed",
                to=to,
                error=str(exc),
            )
            return False
