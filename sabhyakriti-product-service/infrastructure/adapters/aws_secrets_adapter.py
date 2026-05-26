"""AWS Secrets Manager adapter for retrieving secrets at startup."""
from __future__ import annotations

import json

import boto3
import structlog
from botocore.exceptions import ClientError

logger = structlog.get_logger(__name__)


class AWSSecretsAdapter:
    """Fetches secrets from AWS Secrets Manager."""

    def __init__(self, region: str) -> None:
        self._client = boto3.client("secretsmanager", region_name=region)

    def get_secret(self, secret_name: str) -> dict:  # type: ignore[type-arg]
        """Retrieve a secret as a parsed JSON dict.

        Args:
            secret_name: The ARN or name of the secret.

        Returns:
            Dictionary of secret key-value pairs.

        Raises:
            ClientError: If the secret cannot be fetched.
        """
        try:
            response = self._client.get_secret_value(SecretId=secret_name)
            secret_string = response.get("SecretString", "{}")
            parsed: dict = json.loads(secret_string)  # type: ignore[type-arg]
            logger.info("secret_loaded", secret_name=secret_name)
            return parsed
        except ClientError as exc:
            logger.error(
                "secret_load_error", secret_name=secret_name, error=str(exc)
            )
            raise

    def get_secret_value(self, secret_name: str, key: str) -> str:
        """Convenience method to extract a single key from a secret.

        Args:
            secret_name: The ARN or name of the secret.
            key: The key within the secret JSON to return.

        Returns:
            String value for the given key.

        Raises:
            KeyError: If the key is not present in the secret.
        """
        secret = self.get_secret(secret_name)
        return str(secret[key])
