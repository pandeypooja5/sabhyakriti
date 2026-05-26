"""AWS Secrets Manager adapter for retrieving runtime secrets.

Follows the same pattern as Units 1 and 2. Falls back gracefully to
environment variables when running locally without AWS credentials.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_secrets_cache: dict[str, dict[str, Any]] = {}


def get_secret(secret_name: str, region_name: str | None = None) -> dict[str, Any]:
    """Retrieve a secret from AWS Secrets Manager.

    Caches the result in-process to avoid repeated API calls.
    Falls back to environment variables if boto3 is unavailable or
    the secret cannot be fetched (useful for local development).

    Args:
        secret_name: the name or ARN of the secret
        region_name: AWS region; defaults to AWS_REGION env var

    Returns:
        dict of secret key-value pairs
    """
    if secret_name in _secrets_cache:
        return _secrets_cache[secret_name]

    region = region_name or os.getenv("AWS_REGION", "ap-south-1")

    try:
        import boto3
        from botocore.exceptions import ClientError

        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
        secret_string = response.get("SecretString", "{}")
        secrets = json.loads(secret_string)
        _secrets_cache[secret_name] = secrets
        logger.info("Loaded secret '%s' from AWS Secrets Manager", secret_name)
        return secrets

    except ImportError:
        logger.warning("boto3 not available; falling back to environment variables")
        return {}
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Could not fetch secret '%s' from AWS: %s. "
            "Falling back to environment variables.",
            secret_name,
            exc,
        )
        return {}


def load_secrets_to_env(secret_name: str | None = None) -> None:
    """Load secrets from AWS Secrets Manager into os.environ.

    Only loads if SECRET_NAME env var (or explicit argument) is set.
    Called once at application startup inside the lifespan handler.
    """
    name = secret_name or os.getenv("SECRET_NAME")
    if not name:
        logger.debug("No SECRET_NAME configured; skipping AWS Secrets Manager load")
        return

    secrets = get_secret(name)
    for key, value in secrets.items():
        if key not in os.environ:
            os.environ[key] = str(value)
            logger.debug("Loaded secret key '%s' into environment", key)

    logger.info("Secrets loaded from '%s'", name)
