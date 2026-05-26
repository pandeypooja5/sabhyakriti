"""
Unit tests for NotificationApplicationService.

Coverage targets:
- All 13 notification types can be called without raising exceptions
- Email success: SES called, log persisted with SENT
- Email failure (return False): log persisted with FAILED, no exception raised
- Email failure (exception): log persisted with FAILED, no exception raised
- SMS Twilio success: Twilio called, SNS NOT called, log SENT
- SMS Twilio failure -> SNS success: SNS called, log SENT
- SMS both fail: log FAILED, no exception raised
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from application.dtos.notification_dtos import (
    EmailVerificationRequest,
    OrderCancelledRequest,
    OrderConfirmationRequest,
    OrderDeliveredRequest,
    OrderDeliveredSMSRequest,
    OrderItemDTO,
    OrderShippedRequest,
    OrderShippedSMSRequest,
    OTPSMSRequest,
    PaymentReceiptRequest,
    PasswordResetRequest,
    RefundProcessedRequest,
    ReturnApprovedRequest,
    ReturnReceivedRequest,
)
from application.services.notification_application_service import NotificationApplicationService
from domain.value_objects import NotificationChannel, NotificationStatus, NotificationType
from tests.conftest import InMemoryNotificationLogRepository


# ── Helper builders ────────────────────────────────────────────────────────────

def _email_verification_req() -> EmailVerificationRequest:
    return EmailVerificationRequest(
        to_email="user@example.com",
        full_name="Priya Sharma",
        verification_link="https://sabhyakriti.com/verify?token=abc123",
    )


def _password_reset_req() -> PasswordResetRequest:
    return PasswordResetRequest(
        to_email="user@example.com",
        full_name="Priya Sharma",
        reset_link="https://sabhyakriti.com/reset?token=xyz789",
    )


def _order_items() -> list[OrderItemDTO]:
    return [
        OrderItemDTO(
            name="Silk Saree",
            quantity=1,
            unit_price=Decimal("4500.00"),
            total_price=Decimal("4500.00"),
        )
    ]


def _order_confirmation_req() -> OrderConfirmationRequest:
    return OrderConfirmationRequest(
        to_email="user@example.com",
        full_name="Priya Sharma",
        order_number="ORD-001",
        items=_order_items(),
        subtotal=Decimal("4500.00"),
        discount_amount=Decimal("200.00"),
        gst_amount=Decimal("756.00"),
        total=Decimal("5056.00"),
        shipping_address={
            "name": "Priya Sharma",
            "line1": "12 MG Road",
            "city": "Bangalore",
            "state": "Karnataka",
            "pincode": "560001",
            "country": "India",
        },
        payment_method="UPI",
    )


def _order_shipped_req(with_phone: bool = False) -> OrderShippedRequest:
    return OrderShippedRequest(
        to_email="user@example.com",
        to_phone="+919876543210" if with_phone else None,
        full_name="Priya Sharma",
        order_number="ORD-001",
        tracking_number="TRK-99887766",
        courier_name="Delhivery",
    )


def _order_delivered_req(with_phone: bool = False) -> OrderDeliveredRequest:
    return OrderDeliveredRequest(
        to_email="user@example.com",
        to_phone="+919876543210" if with_phone else None,
        full_name="Priya Sharma",
        order_number="ORD-001",
        delivered_at=datetime(2024, 6, 15, 14, 30, tzinfo=timezone.utc),
    )


def _order_cancelled_req() -> OrderCancelledRequest:
    return OrderCancelledRequest(
        to_email="user@example.com",
        full_name="Priya Sharma",
        order_number="ORD-001",
        reason="Customer requested cancellation",
    )


def _return_received_req() -> ReturnReceivedRequest:
    return ReturnReceivedRequest(
        to_email="user@example.com",
        full_name="Priya Sharma",
        order_number="ORD-001",
        return_id="RET-001",
        items=["Silk Saree"],
    )


def _return_approved_req() -> ReturnApprovedRequest:
    return ReturnApprovedRequest(
        to_email="user@example.com",
        full_name="Priya Sharma",
        order_number="ORD-001",
        refund_amount=Decimal("4300.00"),
    )


def _refund_processed_req() -> RefundProcessedRequest:
    return RefundProcessedRequest(
        to_email="user@example.com",
        full_name="Priya Sharma",
        order_number="ORD-001",
        refund_amount=Decimal("4300.00"),
    )


def _payment_receipt_req() -> PaymentReceiptRequest:
    return PaymentReceiptRequest(
        to_email="user@example.com",
        full_name="Priya Sharma",
        order_number="ORD-001",
        payment_id="PAY-001",
        method="UPI",
        amount=Decimal("5056.00"),
        gst_amount=Decimal("756.00"),
        captured_at=datetime(2024, 6, 10, 10, 0, tzinfo=timezone.utc),
    )


def _otp_sms_req() -> OTPSMSRequest:
    return OTPSMSRequest(to_phone="+919876543210", otp_code="482916")


def _order_shipped_sms_req() -> OrderShippedSMSRequest:
    return OrderShippedSMSRequest(
        to_phone="+919876543210",
        order_number="ORD-001",
        courier_name="Delhivery",
        tracking_number="TRK-99887766",
    )


def _order_delivered_sms_req() -> OrderDeliveredSMSRequest:
    return OrderDeliveredSMSRequest(to_phone="+919876543210", order_number="ORD-001")


# ── Tests: all 13 notification types render and dispatch without raising ───────

class TestAllNotificationTypesNoException:
    """Each notification type must complete without raising to the caller."""

    async def test_email_verification(
        self, notification_service: NotificationApplicationService
    ) -> None:
        await notification_service.send_email_verification(_email_verification_req())

    async def test_password_reset(
        self, notification_service: NotificationApplicationService
    ) -> None:
        await notification_service.send_password_reset(_password_reset_req())

    async def test_order_confirmation(
        self, notification_service: NotificationApplicationService
    ) -> None:
        await notification_service.send_order_confirmation(_order_confirmation_req())

    async def test_order_shipped_no_phone(
        self, notification_service: NotificationApplicationService
    ) -> None:
        await notification_service.send_order_shipped(_order_shipped_req(with_phone=False))

    async def test_order_shipped_with_phone(
        self, notification_service: NotificationApplicationService
    ) -> None:
        await notification_service.send_order_shipped(_order_shipped_req(with_phone=True))

    async def test_order_delivered_no_phone(
        self, notification_service: NotificationApplicationService
    ) -> None:
        await notification_service.send_order_delivered(_order_delivered_req(with_phone=False))

    async def test_order_delivered_with_phone(
        self, notification_service: NotificationApplicationService
    ) -> None:
        await notification_service.send_order_delivered(_order_delivered_req(with_phone=True))

    async def test_order_cancelled(
        self, notification_service: NotificationApplicationService
    ) -> None:
        await notification_service.send_order_cancelled(_order_cancelled_req())

    async def test_return_received(
        self, notification_service: NotificationApplicationService
    ) -> None:
        await notification_service.send_return_received(_return_received_req())

    async def test_return_approved(
        self, notification_service: NotificationApplicationService
    ) -> None:
        await notification_service.send_return_approved(_return_approved_req())

    async def test_refund_processed(
        self, notification_service: NotificationApplicationService
    ) -> None:
        await notification_service.send_refund_processed(_refund_processed_req())

    async def test_payment_receipt(
        self, notification_service: NotificationApplicationService
    ) -> None:
        await notification_service.send_payment_receipt(_payment_receipt_req())

    async def test_otp_sms(
        self, notification_service: NotificationApplicationService
    ) -> None:
        await notification_service.send_otp_sms(_otp_sms_req())

    async def test_order_shipped_sms(
        self, notification_service: NotificationApplicationService
    ) -> None:
        await notification_service.send_order_shipped_sms(_order_shipped_sms_req())

    async def test_order_delivered_sms(
        self, notification_service: NotificationApplicationService
    ) -> None:
        await notification_service.send_order_delivered_sms(_order_delivered_sms_req())


# ── Tests: send_email success path ────────────────────────────────────────────

class TestSendEmailSuccess:
    """When SES returns True, a SENT log must be persisted."""

    async def test_ses_called_once(
        self,
        notification_service: NotificationApplicationService,
        mock_ses_adapter: MagicMock,
    ) -> None:
        await notification_service.send_email_verification(_email_verification_req())
        mock_ses_adapter.send_email.assert_awaited_once()

    async def test_log_status_is_sent(
        self,
        notification_service: NotificationApplicationService,
        log_repo: InMemoryNotificationLogRepository,
    ) -> None:
        await notification_service.send_email_verification(_email_verification_req())
        assert len(log_repo.logs) == 1
        assert log_repo.logs[0].status == NotificationStatus.SENT

    async def test_log_channel_is_email(
        self,
        notification_service: NotificationApplicationService,
        log_repo: InMemoryNotificationLogRepository,
    ) -> None:
        await notification_service.send_email_verification(_email_verification_req())
        assert log_repo.logs[0].channel == NotificationChannel.EMAIL

    async def test_log_provider_is_ses(
        self,
        notification_service: NotificationApplicationService,
        log_repo: InMemoryNotificationLogRepository,
    ) -> None:
        await notification_service.send_email_verification(_email_verification_req())
        assert log_repo.logs[0].provider == "SES"

    async def test_log_recipient_matches(
        self,
        notification_service: NotificationApplicationService,
        log_repo: InMemoryNotificationLogRepository,
    ) -> None:
        await notification_service.send_email_verification(_email_verification_req())
        assert log_repo.logs[0].recipient == "user@example.com"


# ── Tests: send_email failure path (returns False) ────────────────────────────

class TestSendEmailFailureReturnFalse:
    """When SES returns False, a FAILED log must be persisted; no exception raised."""

    async def test_no_exception_raised(
        self, service_ses_failing: NotificationApplicationService
    ) -> None:
        # Must not raise
        await service_ses_failing.send_email_verification(_email_verification_req())

    async def test_log_status_is_failed(
        self,
        service_ses_failing: NotificationApplicationService,
        log_repo: InMemoryNotificationLogRepository,
    ) -> None:
        await service_ses_failing.send_email_verification(_email_verification_req())
        assert len(log_repo.logs) == 1
        assert log_repo.logs[0].status == NotificationStatus.FAILED

    async def test_log_has_error_message(
        self,
        service_ses_failing: NotificationApplicationService,
        log_repo: InMemoryNotificationLogRepository,
    ) -> None:
        await service_ses_failing.send_email_verification(_email_verification_req())
        assert log_repo.logs[0].error_message is not None


# ── Tests: send_email failure path (raises exception) ─────────────────────────

class TestSendEmailFailureException:
    """When SES raises an exception, a FAILED log must be persisted; no exception raised."""

    async def test_no_exception_raised(
        self, service_ses_raising: NotificationApplicationService
    ) -> None:
        await service_ses_raising.send_email_verification(_email_verification_req())

    async def test_log_status_is_failed(
        self,
        service_ses_raising: NotificationApplicationService,
        log_repo: InMemoryNotificationLogRepository,
    ) -> None:
        await service_ses_raising.send_email_verification(_email_verification_req())
        assert len(log_repo.logs) == 1
        assert log_repo.logs[0].status == NotificationStatus.FAILED

    async def test_log_captures_exception_message(
        self,
        service_ses_raising: NotificationApplicationService,
        log_repo: InMemoryNotificationLogRepository,
    ) -> None:
        await service_ses_raising.send_email_verification(_email_verification_req())
        assert "SES unavailable" in (log_repo.logs[0].error_message or "")


# ── Tests: SMS Twilio success ──────────────────────────────────────────────────

class TestSMSTwilioSuccess:
    """When Twilio succeeds, SNS must NOT be called; log status is SENT."""

    async def test_twilio_called(
        self,
        notification_service: NotificationApplicationService,
        mock_twilio_adapter: MagicMock,
    ) -> None:
        await notification_service.send_otp_sms(_otp_sms_req())
        mock_twilio_adapter.send_sms.assert_awaited_once()

    async def test_sns_not_called(
        self,
        notification_service: NotificationApplicationService,
        mock_sns_adapter: MagicMock,
    ) -> None:
        await notification_service.send_otp_sms(_otp_sms_req())
        mock_sns_adapter.send_sms.assert_not_awaited()

    async def test_log_status_sent(
        self,
        notification_service: NotificationApplicationService,
        log_repo: InMemoryNotificationLogRepository,
    ) -> None:
        await notification_service.send_otp_sms(_otp_sms_req())
        assert len(log_repo.logs) == 1
        assert log_repo.logs[0].status == NotificationStatus.SENT

    async def test_log_provider_is_twilio(
        self,
        notification_service: NotificationApplicationService,
        log_repo: InMemoryNotificationLogRepository,
    ) -> None:
        await notification_service.send_otp_sms(_otp_sms_req())
        assert log_repo.logs[0].provider == "TWILIO"


# ── Tests: SMS Twilio failure -> SNS success ──────────────────────────────────

class TestSMSTwilioFailoverToSNS:
    """When Twilio fails, SNS must be called; log status is SENT from SNS."""

    async def test_sns_called_on_twilio_failure(
        self,
        service_twilio_failing_sns_ok: NotificationApplicationService,
        mock_sns_adapter: MagicMock,
    ) -> None:
        await service_twilio_failing_sns_ok.send_otp_sms(_otp_sms_req())
        mock_sns_adapter.send_sms.assert_awaited_once()

    async def test_log_status_sent_via_sns(
        self,
        service_twilio_failing_sns_ok: NotificationApplicationService,
        log_repo: InMemoryNotificationLogRepository,
    ) -> None:
        await service_twilio_failing_sns_ok.send_otp_sms(_otp_sms_req())
        assert len(log_repo.logs) == 1
        assert log_repo.logs[0].status == NotificationStatus.SENT

    async def test_log_provider_is_sns(
        self,
        service_twilio_failing_sns_ok: NotificationApplicationService,
        log_repo: InMemoryNotificationLogRepository,
    ) -> None:
        await service_twilio_failing_sns_ok.send_otp_sms(_otp_sms_req())
        assert log_repo.logs[0].provider == "SNS"

    async def test_sns_called_on_twilio_exception(
        self,
        service_twilio_raising_sns_ok: NotificationApplicationService,
        mock_sns_adapter: MagicMock,
    ) -> None:
        await service_twilio_raising_sns_ok.send_otp_sms(_otp_sms_req())
        mock_sns_adapter.send_sms.assert_awaited_once()


# ── Tests: SMS both providers fail ────────────────────────────────────────────

class TestSMSAllProvidersFail:
    """When both Twilio and SNS fail, log status is FAILED; no exception raised."""

    async def test_no_exception_raised(
        self, service_all_sms_failing: NotificationApplicationService
    ) -> None:
        await service_all_sms_failing.send_otp_sms(_otp_sms_req())

    async def test_log_status_is_failed(
        self,
        service_all_sms_failing: NotificationApplicationService,
        log_repo: InMemoryNotificationLogRepository,
    ) -> None:
        await service_all_sms_failing.send_otp_sms(_otp_sms_req())
        assert len(log_repo.logs) == 1
        assert log_repo.logs[0].status == NotificationStatus.FAILED


# ── Tests: exception safety (all methods must swallow exceptions) ─────────────

class TestExceptionSafety:
    """No notification method should propagate any exception to the caller."""

    async def test_send_email_verification_never_raises(
        self, service_ses_raising: NotificationApplicationService
    ) -> None:
        await service_ses_raising.send_email_verification(_email_verification_req())

    async def test_send_password_reset_never_raises(
        self, service_ses_raising: NotificationApplicationService
    ) -> None:
        await service_ses_raising.send_password_reset(_password_reset_req())

    async def test_send_order_confirmation_never_raises(
        self, service_ses_raising: NotificationApplicationService
    ) -> None:
        await service_ses_raising.send_order_confirmation(_order_confirmation_req())

    async def test_send_order_shipped_never_raises(
        self, service_ses_raising: NotificationApplicationService
    ) -> None:
        await service_ses_raising.send_order_shipped(_order_shipped_req())

    async def test_send_order_delivered_never_raises(
        self, service_ses_raising: NotificationApplicationService
    ) -> None:
        await service_ses_raising.send_order_delivered(_order_delivered_req())

    async def test_send_order_cancelled_never_raises(
        self, service_ses_raising: NotificationApplicationService
    ) -> None:
        await service_ses_raising.send_order_cancelled(_order_cancelled_req())

    async def test_send_return_received_never_raises(
        self, service_ses_raising: NotificationApplicationService
    ) -> None:
        await service_ses_raising.send_return_received(_return_received_req())

    async def test_send_return_approved_never_raises(
        self, service_ses_raising: NotificationApplicationService
    ) -> None:
        await service_ses_raising.send_return_approved(_return_approved_req())

    async def test_send_refund_processed_never_raises(
        self, service_ses_raising: NotificationApplicationService
    ) -> None:
        await service_ses_raising.send_refund_processed(_refund_processed_req())

    async def test_send_payment_receipt_never_raises(
        self, service_ses_raising: NotificationApplicationService
    ) -> None:
        await service_ses_raising.send_payment_receipt(_payment_receipt_req())

    async def test_send_otp_sms_never_raises(
        self, service_all_sms_failing: NotificationApplicationService
    ) -> None:
        await service_all_sms_failing.send_otp_sms(_otp_sms_req())

    async def test_send_order_shipped_sms_never_raises(
        self, service_all_sms_failing: NotificationApplicationService
    ) -> None:
        await service_all_sms_failing.send_order_shipped_sms(_order_shipped_sms_req())

    async def test_send_order_delivered_sms_never_raises(
        self, service_all_sms_failing: NotificationApplicationService
    ) -> None:
        await service_all_sms_failing.send_order_delivered_sms(_order_delivered_sms_req())
