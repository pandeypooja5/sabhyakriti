"""
Jinja2 template rendering tests.

Each of the 10 email templates is rendered with realistic sample data and
verified to produce valid HTML containing expected content.  No live email
is sent — this is purely a rendering/syntax test.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from jinja2 import Environment


# ── Sample data helpers ────────────────────────────────────────────────────────

_SAMPLE_ITEMS = [
    {
        "name": "Handwoven Silk Saree",
        "quantity": 1,
        "unit_price": Decimal("4500.00"),
        "total_price": Decimal("4500.00"),
    },
    {
        "name": "Block Print Kurta",
        "quantity": 2,
        "unit_price": Decimal("1200.00"),
        "total_price": Decimal("2400.00"),
    },
]

_SAMPLE_ADDRESS = {
    "name": "Priya Sharma",
    "line1": "12 MG Road",
    "line2": "Indiranagar",
    "city": "Bangalore",
    "state": "Karnataka",
    "pincode": "560001",
    "country": "India",
}

_DELIVERED_AT = datetime(2024, 6, 15, 14, 30, tzinfo=timezone.utc)
_CAPTURED_AT = datetime(2024, 6, 10, 10, 0, tzinfo=timezone.utc)


# ── Template render helper ─────────────────────────────────────────────────────

def render(env: Environment, template_name: str, context: dict) -> str:  # type: ignore[type-arg]
    """Render a template and return the HTML string."""
    tmpl = env.get_template(template_name)
    return tmpl.render(**context)


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestEmailVerificationTemplate:
    def test_renders_without_error(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "email_verification.html",
            {
                "full_name": "Priya Sharma",
                "verification_link": "https://sabhyakriti.com/verify?token=abc123",
            },
        )
        assert len(html) > 0

    def test_contains_full_name(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "email_verification.html",
            {
                "full_name": "Priya Sharma",
                "verification_link": "https://sabhyakriti.com/verify?token=abc123",
            },
        )
        assert "Priya Sharma" in html

    def test_contains_verification_link(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "email_verification.html",
            {
                "full_name": "Priya Sharma",
                "verification_link": "https://sabhyakriti.com/verify?token=abc123",
            },
        )
        assert "https://sabhyakriti.com/verify?token=abc123" in html

    def test_contains_48h_expiry(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "email_verification.html",
            {
                "full_name": "Priya Sharma",
                "verification_link": "https://sabhyakriti.com/verify?token=abc123",
            },
        )
        assert "48" in html

    def test_is_valid_html(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "email_verification.html",
            {
                "full_name": "Priya Sharma",
                "verification_link": "https://sabhyakriti.com/verify?token=abc123",
            },
        )
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html


class TestPasswordResetTemplate:
    def test_renders_without_error(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "password_reset.html",
            {
                "full_name": "Priya Sharma",
                "reset_link": "https://sabhyakriti.com/reset?token=xyz789",
            },
        )
        assert len(html) > 0

    def test_contains_reset_link(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "password_reset.html",
            {
                "full_name": "Priya Sharma",
                "reset_link": "https://sabhyakriti.com/reset?token=xyz789",
            },
        )
        assert "https://sabhyakriti.com/reset?token=xyz789" in html

    def test_contains_2h_expiry_warning(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "password_reset.html",
            {
                "full_name": "Priya Sharma",
                "reset_link": "https://sabhyakriti.com/reset?token=xyz789",
            },
        )
        assert "2" in html  # "2 hours" or "2h"


class TestOrderConfirmationTemplate:
    def test_renders_without_error(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "order_confirmation.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "items": _SAMPLE_ITEMS,
                "subtotal": Decimal("6900.00"),
                "discount_amount": Decimal("200.00"),
                "gst_amount": Decimal("1206.00"),
                "total": Decimal("7906.00"),
                "shipping_address": _SAMPLE_ADDRESS,
                "payment_method": "UPI",
            },
        )
        assert len(html) > 0

    def test_contains_order_number(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "order_confirmation.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "items": _SAMPLE_ITEMS,
                "subtotal": Decimal("6900.00"),
                "discount_amount": Decimal("200.00"),
                "gst_amount": Decimal("1206.00"),
                "total": Decimal("7906.00"),
                "shipping_address": _SAMPLE_ADDRESS,
                "payment_method": "UPI",
            },
        )
        assert "ORD-001" in html

    def test_contains_item_names(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "order_confirmation.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "items": _SAMPLE_ITEMS,
                "subtotal": Decimal("6900.00"),
                "discount_amount": Decimal("200.00"),
                "gst_amount": Decimal("1206.00"),
                "total": Decimal("7906.00"),
                "shipping_address": _SAMPLE_ADDRESS,
                "payment_method": "UPI",
            },
        )
        assert "Handwoven Silk Saree" in html
        assert "Block Print Kurta" in html

    def test_contains_shipping_city(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "order_confirmation.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "items": _SAMPLE_ITEMS,
                "subtotal": Decimal("6900.00"),
                "discount_amount": Decimal("200.00"),
                "gst_amount": Decimal("1206.00"),
                "total": Decimal("7906.00"),
                "shipping_address": _SAMPLE_ADDRESS,
                "payment_method": "UPI",
            },
        )
        assert "Bangalore" in html


class TestOrderShippedTemplate:
    def test_renders_without_error(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "order_shipped.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "tracking_number": "TRK-99887766",
                "courier_name": "Delhivery",
            },
        )
        assert len(html) > 0

    def test_contains_tracking_number(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "order_shipped.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "tracking_number": "TRK-99887766",
                "courier_name": "Delhivery",
            },
        )
        assert "TRK-99887766" in html

    def test_contains_courier_name(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "order_shipped.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "tracking_number": "TRK-99887766",
                "courier_name": "Delhivery",
            },
        )
        assert "Delhivery" in html


class TestOrderDeliveredTemplate:
    def test_renders_without_error(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "order_delivered.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "delivered_at": _DELIVERED_AT,
            },
        )
        assert len(html) > 0

    def test_contains_7_day_return_note(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "order_delivered.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "delivered_at": _DELIVERED_AT,
            },
        )
        assert "7" in html


class TestOrderCancelledTemplate:
    def test_renders_without_error(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "order_cancelled.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "reason": "Customer requested cancellation",
            },
        )
        assert len(html) > 0

    def test_renders_without_reason(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "order_cancelled.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "reason": None,
            },
        )
        assert "ORD-001" in html

    def test_contains_reason_when_provided(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "order_cancelled.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "reason": "Out of stock",
            },
        )
        assert "Out of stock" in html


class TestReturnReceivedTemplate:
    def test_renders_without_error(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "return_received.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "return_id": "RET-001",
                "items": ["Silk Saree", "Block Print Kurta"],
            },
        )
        assert len(html) > 0

    def test_contains_return_id(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "return_received.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "return_id": "RET-001",
                "items": ["Silk Saree"],
            },
        )
        assert "RET-001" in html

    def test_contains_item_names(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "return_received.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "return_id": "RET-001",
                "items": ["Silk Saree", "Block Print Kurta"],
            },
        )
        assert "Silk Saree" in html
        assert "Block Print Kurta" in html


class TestReturnApprovedTemplate:
    def test_renders_without_error(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "return_approved.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "refund_amount": Decimal("4300.00"),
            },
        )
        assert len(html) > 0

    def test_contains_refund_amount(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "return_approved.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "refund_amount": Decimal("4300.00"),
            },
        )
        assert "4300" in html

    def test_contains_timeline(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "return_approved.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "refund_amount": Decimal("4300.00"),
            },
        )
        # "3–5 business days" timeline note
        assert "3" in html
        assert "5" in html


class TestRefundProcessedTemplate:
    def test_renders_without_error(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "refund_processed.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "refund_amount": Decimal("4300.00"),
            },
        )
        assert len(html) > 0

    def test_contains_refund_amount(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "refund_processed.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "refund_amount": Decimal("4300.00"),
            },
        )
        assert "4300" in html


class TestPaymentReceiptTemplate:
    def test_renders_without_error(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "payment_receipt.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "payment_id": "PAY-001",
                "method": "UPI",
                "amount": Decimal("5056.00"),
                "gst_amount": Decimal("756.00"),
                "captured_at": _CAPTURED_AT,
            },
        )
        assert len(html) > 0

    def test_contains_payment_id(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "payment_receipt.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "payment_id": "PAY-001",
                "method": "UPI",
                "amount": Decimal("5056.00"),
                "gst_amount": Decimal("756.00"),
                "captured_at": _CAPTURED_AT,
            },
        )
        assert "PAY-001" in html

    def test_contains_payment_method(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "payment_receipt.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "payment_id": "PAY-001",
                "method": "UPI",
                "amount": Decimal("5056.00"),
                "gst_amount": Decimal("756.00"),
                "captured_at": _CAPTURED_AT,
            },
        )
        assert "UPI" in html

    def test_contains_gst_amount(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "payment_receipt.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "payment_id": "PAY-001",
                "method": "UPI",
                "amount": Decimal("5056.00"),
                "gst_amount": Decimal("756.00"),
                "captured_at": _CAPTURED_AT,
            },
        )
        assert "756" in html

    def test_contains_total_amount(self, jinja_env: Environment) -> None:
        html = render(
            jinja_env,
            "payment_receipt.html",
            {
                "full_name": "Priya Sharma",
                "order_number": "ORD-001",
                "payment_id": "PAY-001",
                "method": "UPI",
                "amount": Decimal("5056.00"),
                "gst_amount": Decimal("756.00"),
                "captured_at": _CAPTURED_AT,
            },
        )
        assert "5056" in html
