"""Tests for the domain signature service.

Includes both property-based tests (Hypothesis) and deterministic unit tests.
"""

from __future__ import annotations

import hashlib
import hmac

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from domain.services.signature_service import (
    verify_payment_signature,
    verify_webhook_signature,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_payment_sig(key: str, order_id: str, payment_id: str) -> str:
    msg = f"{order_id}|{payment_id}".encode()
    return hmac.new(key.encode(), msg, hashlib.sha256).hexdigest()


def _make_webhook_sig(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


# ---------------------------------------------------------------------------
# Property-based tests — payment signature
# ---------------------------------------------------------------------------

_printable = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), min_codepoints=33),
    min_size=1,
    max_size=50,
)


@given(key=_printable, order_id=_printable, payment_id=_printable)
@settings(max_examples=200)
def test_payment_signature_roundtrip(key: str, order_id: str, payment_id: str) -> None:
    """Property: sign(key, oid, pid) verified with same inputs always returns True."""
    sig = _make_payment_sig(key, order_id, payment_id)
    assert verify_payment_signature(key, order_id, payment_id, sig) is True


@given(
    key=_printable,
    order_id=_printable,
    payment_id=_printable,
    tamper=_printable,
)
@settings(max_examples=200)
def test_payment_signature_tampered_is_false(
    key: str, order_id: str, payment_id: str, tamper: str
) -> None:
    """Property: any tampered signature (not derived from the same inputs) is rejected."""
    correct_sig = _make_payment_sig(key, order_id, payment_id)
    assume(tamper != correct_sig)
    assert verify_payment_signature(key, order_id, payment_id, tamper) is False


@given(
    key=_printable,
    wrong_key=_printable,
    order_id=_printable,
    payment_id=_printable,
)
@settings(max_examples=200)
def test_payment_signature_wrong_key_is_false(
    key: str, wrong_key: str, order_id: str, payment_id: str
) -> None:
    """Property: a signature computed with key1 is not valid under key2."""
    assume(key != wrong_key)
    sig = _make_payment_sig(key, order_id, payment_id)
    assert verify_payment_signature(wrong_key, order_id, payment_id, sig) is False


# ---------------------------------------------------------------------------
# Unit tests — webhook signature with known test vectors
# ---------------------------------------------------------------------------


def test_webhook_signature_valid_known_vector() -> None:
    """Verify a known-good HMAC-SHA256 webhook signature."""
    secret = "webhook_secret_abc"
    body = b'{"event":"payment.captured","id":"evt_001"}'
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_webhook_signature(secret, body, expected) is True


def test_webhook_signature_invalid_sig() -> None:
    """An incorrect webhook signature must be rejected."""
    secret = "webhook_secret_abc"
    body = b'{"event":"payment.captured","id":"evt_001"}'
    assert verify_webhook_signature(secret, body, "deadbeef" * 8) is False


def test_webhook_signature_wrong_secret() -> None:
    """A signature computed with the wrong secret must be rejected."""
    body = b'{"event":"payment.captured"}'
    sig = _make_webhook_sig("correct_secret", body)
    assert verify_webhook_signature("wrong_secret", body, sig) is False


def test_webhook_signature_empty_body() -> None:
    """Edge case: empty body with a valid signature computed from empty body."""
    secret = "s3cr3t"
    body = b""
    sig = _make_webhook_sig(secret, body)
    assert verify_webhook_signature(secret, body, sig) is True


def test_webhook_signature_body_mutation_invalidates() -> None:
    """Mutating the body after computing the signature must fail verification."""
    secret = "s3cr3t"
    original = b'{"amount":100}'
    sig = _make_webhook_sig(secret, original)
    mutated = b'{"amount":999}'
    assert verify_webhook_signature(secret, mutated, sig) is False


# ---------------------------------------------------------------------------
# Property-based tests — webhook signature
# ---------------------------------------------------------------------------


@given(secret=_printable, body=st.binary(min_size=0, max_size=256))
@settings(max_examples=200)
def test_webhook_signature_roundtrip(secret: str, body: bytes) -> None:
    """Property: compute-then-verify round trip always succeeds."""
    sig = _make_webhook_sig(secret, body)
    assert verify_webhook_signature(secret, body, sig) is True
