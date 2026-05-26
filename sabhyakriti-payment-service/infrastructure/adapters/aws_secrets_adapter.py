"""AWS Secrets Manager adapter.

Secrets are retrieved once at startup via ``load_razorpay_secrets`` and
cached in memory for the process lifetime. All boto3 calls are wrapped in
a thread-pool executor to keep the async event loop unblocked.
"""

from __future__ import annotations

import asyncio
import functools
from dataclasses import dataclass

import boto3
import structlog

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class RazorpaySecrets:
    """Container for Razorpay credentials loaded from AWS Secrets Manager."""

    key_id: str
    key_secret: str
    webhook_secret: str


class AWSSecretsAdapter:
    """Async wrapper around the synchronous boto3 Secrets Manager client."""

    def __init__(self, region_name: str) -> None:
        self._client = boto3.client("secretsmanager", region_name=region_name)

    async def get_secret_value(self, secret_name: str) -> str:
        """Fetch a plaintext secret string from AWS Secrets Manager.

        Args:
            secret_name: The name or ARN of the secret.

        Returns:
            The plaintext secret value.

        Raises:
            RuntimeError: If the secret cannot be retrieved.
        """
        loop = asyncio.get_event_loop()
        logger.info("fetching_secret", secret_name=secret_name)
        try:
            response: dict = await loop.run_in_executor(  # type: ignore[type-arg]
                None,
                functools.partial(
                    self._client.get_secret_value,
                    SecretId=secret_name,
                ),
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to load secret '{secret_name}': {exc}") from exc

        secret = response.get("SecretString")
        if not secret:
            raise RuntimeError(f"Secret '{secret_name}' has no SecretString value.")
        return secret

    async def load_razorpay_secrets(
        self,
        key_id_secret_name: str,
        key_secret_secret_name: str,
        webhook_secret_secret_name: str,
    ) -> RazorpaySecrets:
        """Load all three Razorpay secrets concurrently.

        Args:
            key_id_secret_name: AWS secret name holding the Razorpay key ID.
            key_secret_secret_name: AWS secret name holding the Razorpay key secret.
            webhook_secret_secret_name: AWS secret name holding the webhook secret.

        Returns:
            A populated ``RazorpaySecrets`` dataclass.
        """
        key_id, key_secret, webhook_secret = await asyncio.gather(
            self.get_secret_value(key_id_secret_name),
            self.get_secret_value(key_secret_secret_name),
            self.get_secret_value(webhook_secret_secret_name),
        )
        logger.info("razorpay_secrets_loaded")
        return RazorpaySecrets(
            key_id=key_id.strip(),
            key_secret=key_secret.strip(),
            webhook_secret=webhook_secret.strip(),
        )
