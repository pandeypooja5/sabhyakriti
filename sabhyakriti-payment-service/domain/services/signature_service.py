"""Domain service for HMAC-SHA256 signature verification.

All comparisons use ``hmac.compare_digest`` to prevent timing-based
side-channel attacks.
"""

from __future__ import annotations

import hashlib
import hmac


def verify_payment_signature(
    key_secret: str,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    signature: str,
) -> bool:
    """Verify the HMAC-SHA256 signature returned by Razorpay after payment.

    The message to sign is ``"{razorpay_order_id}|{razorpay_payment_id}"``.

    Args:
        key_secret: Razorpay API key secret.
        razorpay_order_id: The Razorpay order ID (``order_XXXX``).
        razorpay_payment_id: The Razorpay payment ID (``pay_XXXX``).
        signature: The ``razorpay_signature`` value from the callback.

    Returns:
        ``True`` if the signature is valid, ``False`` otherwise.
    """
    message = f"{razorpay_order_id}|{razorpay_payment_id}".encode()
    expected = hmac.new(
        key_secret.encode(),
        message,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def verify_webhook_signature(
    webhook_secret: str,
    raw_body: bytes,
    signature: str,
) -> bool:
    """Verify the HMAC-SHA256 signature of an incoming Razorpay webhook.

    Compares the ``X-Razorpay-Signature`` header value against a freshly
    computed HMAC over the raw request body bytes.

    Args:
        webhook_secret: Razorpay webhook secret configured in the dashboard.
        raw_body: The raw (un-parsed) request body bytes.
        signature: The value of the ``X-Razorpay-Signature`` HTTP header.

    Returns:
        ``True`` if the signature is valid, ``False`` otherwise.
    """
    expected = hmac.new(
        webhook_secret.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
