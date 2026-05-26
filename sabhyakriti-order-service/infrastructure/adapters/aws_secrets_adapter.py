"""
AWS Secrets Manager adapter.

Provides a single fetch_secret() helper with caching to avoid excessive
Secrets Manager API calls on every request.
"""

from __future__ import annotations

import json
import threading
import time
from typing import Any

import boto3
import structlog
from botocore.exceptions import ClientError

logger = structlog.get_logger(__name__)

_CACHE_TTL_SECONDS = 300  # 5 minutes
_cache: dict[str, tuple[Any, float]] = {}
_cache_lock = threading.Lock()


def fetch_secret(secret_name: str, region_name: str = "ap-south-1") -> Any:
    """
    Fetch a secret from AWS Secrets Manager with in-process caching.

    Returns the parsed JSON value (dict) or raw string.
    """
    now = time.monotonic()

    with _cache_lock:
        if secret_name in _cache:
            value, cached_at = _cache[secret_name]
            if now - cached_at < _CACHE_TTL_SECONDS:
                return value

    try:
        client = boto3.client("secretsmanager", region_name=region_name)
        response: dict[str, Any] = client.get_secret_value(SecretId=secret_name)

        secret_string = response.get("SecretString")
        if secret_string:
            try:
                value = json.loads(secret_string)
            except json.JSONDecodeError:
                value = secret_string
        else:
            value = response.get("SecretBinary", b"")

    except ClientError:
        logger.exception("secrets_manager_fetch_failed", secret_name=secret_name)
        raise

    with _cache_lock:
        _cache[secret_name] = (value, now)

    return value
