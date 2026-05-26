"""Tests for Coupon.is_valid() — parametrized edge cases."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from domain.entities.coupon import Coupon
from domain.value_objects import CouponType
from tests.conftest import make_coupon

_NOW = datetime(2026, 5, 21, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Parametrized validity tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "coupon_kwargs, now, subtotal, expected_valid, expected_error_fragment",
    [
        # ---- Valid cases ----
        pytest.param(
            {"is_active": True, "expires_at": None, "max_uses": None, "used_count": 0, "min_order_amount": Decimal("0")},
            _NOW,
            Decimal("500"),
            True,
            "",
            id="all_valid_no_expiry_no_limit",
        ),
        pytest.param(
            {
                "is_active": True,
                "expires_at": _NOW + timedelta(days=1),
                "max_uses": 100,
                "used_count": 50,
                "min_order_amount": Decimal("100"),
            },
            _NOW,
            Decimal("500"),
            True,
            "",
            id="all_valid_with_expiry_and_limit",
        ),
        # ---- Inactive coupon ----
        pytest.param(
            {"is_active": False},
            _NOW,
            Decimal("500"),
            False,
            "not active",
            id="inactive_coupon",
        ),
        # ---- Expired coupon ----
        pytest.param(
            {"is_active": True, "expires_at": _NOW - timedelta(seconds=1)},
            _NOW,
            Decimal("500"),
            False,
            "expired",
            id="expired_coupon",
        ),
        # ---- Max uses reached ----
        pytest.param(
            {"is_active": True, "expires_at": None, "max_uses": 10, "used_count": 10},
            _NOW,
            Decimal("500"),
            False,
            "usage limit",
            id="max_uses_reached",
        ),
        pytest.param(
            {"is_active": True, "expires_at": None, "max_uses": 10, "used_count": 11},
            _NOW,
            Decimal("500"),
            False,
            "usage limit",
            id="used_count_exceeds_max",
        ),
        # ---- Below min order amount ----
        pytest.param(
            {"is_active": True, "expires_at": None, "max_uses": None, "min_order_amount": Decimal("1000")},
            _NOW,
            Decimal("999"),
            False,
            "Minimum order amount",
            id="below_min_order_amount",
        ),
        # ---- Exactly at min order amount — valid ----
        pytest.param(
            {"is_active": True, "expires_at": None, "max_uses": None, "min_order_amount": Decimal("500")},
            _NOW,
            Decimal("500"),
            True,
            "",
            id="exactly_at_min_order_amount",
        ),
        # ---- Expires exactly at now — expired (strictly after) ----
        pytest.param(
            {"is_active": True, "expires_at": _NOW},
            _NOW + timedelta(seconds=1),
            Decimal("500"),
            False,
            "expired",
            id="expires_at_boundary",
        ),
    ],
)
def test_coupon_is_valid(
    coupon_kwargs: dict,
    now: datetime,
    subtotal: Decimal,
    expected_valid: bool,
    expected_error_fragment: str,
) -> None:
    """Coupon.is_valid returns (True, '') or (False, error_message) correctly."""
    coupon = make_coupon(**coupon_kwargs)
    valid, message = coupon.is_valid(now, subtotal)

    assert valid is expected_valid, (
        f"Expected valid={expected_valid} but got valid={valid} "
        f"(message: '{message}')"
    )

    if not expected_valid:
        assert expected_error_fragment.lower() in message.lower(), (
            f"Expected error fragment '{expected_error_fragment}' "
            f"not found in '{message}'"
        )
    else:
        assert message == ""


def test_coupon_valid_with_max_uses_exactly_one_remaining() -> None:
    """Coupon with used_count = max_uses - 1 is still valid."""
    coupon = make_coupon(max_uses=10, used_count=9)
    valid, msg = coupon.is_valid(_NOW, Decimal("500"))
    assert valid is True
    assert msg == ""


def test_flat_coupon_zero_min_order_any_subtotal_valid() -> None:
    """FLAT coupon with no min_order_amount is valid for any subtotal >= 0."""
    coupon = make_coupon(
        coupon_type=CouponType.FLAT,
        min_order_amount=Decimal("0"),
    )
    valid, _ = coupon.is_valid(_NOW, Decimal("0.01"))
    assert valid is True


def test_percent_coupon_validation() -> None:
    """PERCENT coupon validates the same way as FLAT."""
    coupon = make_coupon(
        coupon_type=CouponType.PERCENT,
        value=Decimal("15"),
        min_order_amount=Decimal("200"),
    )
    valid, _ = coupon.is_valid(_NOW, Decimal("199"))
    assert valid is False

    valid2, _ = coupon.is_valid(_NOW, Decimal("200"))
    assert valid2 is True
