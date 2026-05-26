"""
NotificationApplicationService — orchestrates template rendering, adapter calls,
retry logic, and persistence logging for all notification types.

All public methods are fire-and-forget: they NEVER raise exceptions to callers.
Errors are logged to structlog (CloudWatch) and persisted in notification_logs.
"""

from __future__ import annotations

import structlog
from jinja2 import Environment

from application.dtos.notification_dtos import (
    EmailVerificationRequest,
    OrderCancelledRequest,
    OrderConfirmationRequest,
    OrderDeliveredRequest,
    OrderDeliveredSMSRequest,
    OrderShippedRequest,
    OrderShippedSMSRequest,
    OTPSMSRequest,
    PaymentReceiptRequest,
    PasswordResetRequest,
    RefundProcessedRequest,
    ReturnApprovedRequest,
    ReturnReceivedRequest,
)
from domain.entities.notification_log import NotificationLog
from domain.repositories.i_notification_log_repository import INotificationLogRepository
from domain.value_objects import NotificationChannel, NotificationStatus, NotificationType

logger = structlog.get_logger(__name__)


class NotificationApplicationService:
    """
    Application-layer service owning all notification orchestration.

    Injected dependencies (all are protocol-compatible so tests can mock them):
    - jinja_env:      Jinja2 Environment with templates loaded
    - ses_adapter:    AWS SES email adapter
    - twilio_adapter: Twilio SMS adapter (primary)
    - sns_adapter:    AWS SNS SMS adapter (fallback)
    - log_repo:       Persistence repository for notification_logs
    """

    def __init__(
        self,
        jinja_env: Environment,
        ses_adapter: object,
        twilio_adapter: object,
        sns_adapter: object,
        log_repo: INotificationLogRepository,
    ) -> None:
        self._jinja = jinja_env
        self._ses = ses_adapter  # type: ignore[assignment]
        self._twilio = twilio_adapter  # type: ignore[assignment]
        self._sns = sns_adapter  # type: ignore[assignment]
        self._log_repo = log_repo

    # ── Private Helpers ────────────────────────────────────────────────────────

    def _render(self, template_name: str, context: dict) -> str:  # type: ignore[type-arg]
        """Render a Jinja2 template and return the HTML string."""
        tmpl = self._jinja.get_template(template_name)
        return tmpl.render(**context)

    async def _persist_log(self, log: NotificationLog) -> None:
        """Best-effort log persistence — never propagates exceptions."""
        try:
            await self._log_repo.create(log)
        except Exception as exc:
            logger.error(
                "notification_log_persistence_failed",
                error=str(exc),
                notification_type=log.notification_type,
                recipient=log.recipient,
            )

    async def _send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        notification_type: NotificationType,
    ) -> None:
        """
        Send an email via SES with retry.  Always resolves; never raises.
        Persists a SENT or FAILED NotificationLog entry.
        """
        provider = "SES"
        status = NotificationStatus.FAILED
        error_message: str | None = None

        try:
            success: bool = await self._ses.send_email(  # type: ignore[attr-defined]
                to=to,
                from_email=None,  # adapter uses config default
                subject=subject,
                html_body=html_body,
            )
            if success:
                status = NotificationStatus.SENT
                logger.info(
                    "email_sent",
                    recipient=to,
                    notification_type=notification_type,
                    provider=provider,
                )
            else:
                error_message = "SES returned failure without exception"
                logger.warning(
                    "email_send_failed",
                    recipient=to,
                    notification_type=notification_type,
                    provider=provider,
                    error=error_message,
                )
        except Exception as exc:
            error_message = str(exc)
            logger.error(
                "email_send_exception",
                recipient=to,
                notification_type=notification_type,
                provider=provider,
                error=error_message,
                exc_info=True,
            )

        await self._persist_log(
            NotificationLog(
                notification_type=notification_type,
                channel=NotificationChannel.EMAIL,
                recipient=to,
                status=status,
                provider=provider,
                error_message=error_message,
            )
        )

    async def _send_sms(
        self,
        to_phone: str,
        message: str,
        notification_type: NotificationType,
    ) -> None:
        """
        Send an SMS via Twilio (primary).  If Twilio fails, falls back to SNS.
        Always resolves; never raises.
        Persists a SENT or FAILED NotificationLog entry.
        """
        provider = "TWILIO"
        status = NotificationStatus.FAILED
        error_message: str | None = None

        # ── Primary: Twilio ────────────────────────────────────────────────────
        try:
            twilio_ok: bool = await self._twilio.send_sms(  # type: ignore[attr-defined]
                to=to_phone,
                message=message,
            )
            if twilio_ok:
                status = NotificationStatus.SENT
                logger.info(
                    "sms_sent",
                    recipient=to_phone,
                    notification_type=notification_type,
                    provider=provider,
                )
                await self._persist_log(
                    NotificationLog(
                        notification_type=notification_type,
                        channel=NotificationChannel.SMS,
                        recipient=to_phone,
                        status=status,
                        provider=provider,
                    )
                )
                return
            else:
                error_message = "Twilio returned failure without exception"
        except Exception as exc:
            error_message = str(exc)
            logger.warning(
                "twilio_sms_failed_falling_back_to_sns",
                recipient=to_phone,
                notification_type=notification_type,
                error=error_message,
            )

        # ── Fallback: AWS SNS ──────────────────────────────────────────────────
        provider = "SNS"
        try:
            sns_ok: bool = await self._sns.send_sms(  # type: ignore[attr-defined]
                to=to_phone,
                message=message,
            )
            if sns_ok:
                status = NotificationStatus.SENT
                error_message = None
                logger.info(
                    "sms_sent_via_sns_fallback",
                    recipient=to_phone,
                    notification_type=notification_type,
                    provider=provider,
                )
            else:
                logger.error(
                    "sns_sms_fallback_also_failed",
                    recipient=to_phone,
                    notification_type=notification_type,
                    provider=provider,
                )
        except Exception as exc:
            error_message = f"Twilio: {error_message} | SNS: {exc}"
            logger.error(
                "sms_all_providers_failed",
                recipient=to_phone,
                notification_type=notification_type,
                error=error_message,
                exc_info=True,
            )

        await self._persist_log(
            NotificationLog(
                notification_type=notification_type,
                channel=NotificationChannel.SMS,
                recipient=to_phone,
                status=status,
                provider=provider,
                error_message=error_message,
            )
        )

    # ── Email Notification Methods ─────────────────────────────────────────────

    async def send_email_verification(self, req: EmailVerificationRequest) -> None:
        """Send account email-verification link."""
        try:
            html = self._render(
                "email_verification.html",
                {"full_name": req.full_name, "verification_link": req.verification_link},
            )
        except Exception as exc:
            logger.error("template_render_failed", template="email_verification.html", error=str(exc))
            return
        await self._send_email(
            to=str(req.to_email),
            subject="Verify your Sabhyakriti email address",
            html_body=html,
            notification_type=NotificationType.EMAIL_VERIFICATION,
        )

    async def send_password_reset(self, req: PasswordResetRequest) -> None:
        """Send password-reset link email."""
        try:
            html = self._render(
                "password_reset.html",
                {"full_name": req.full_name, "reset_link": req.reset_link},
            )
        except Exception as exc:
            logger.error("template_render_failed", template="password_reset.html", error=str(exc))
            return
        await self._send_email(
            to=str(req.to_email),
            subject="Reset your Sabhyakriti password",
            html_body=html,
            notification_type=NotificationType.PASSWORD_RESET,
        )

    async def send_order_confirmation(self, req: OrderConfirmationRequest) -> None:
        """Send order-confirmation email with full order summary."""
        try:
            html = self._render(
                "order_confirmation.html",
                {
                    "full_name": req.full_name,
                    "order_number": req.order_number,
                    "items": req.items,
                    "subtotal": req.subtotal,
                    "discount_amount": req.discount_amount,
                    "gst_amount": req.gst_amount,
                    "total": req.total,
                    "shipping_address": req.shipping_address,
                    "payment_method": req.payment_method,
                },
            )
        except Exception as exc:
            logger.error("template_render_failed", template="order_confirmation.html", error=str(exc))
            return
        await self._send_email(
            to=str(req.to_email),
            subject=f"Order #{req.order_number} Confirmed — Sabhyakriti",
            html_body=html,
            notification_type=NotificationType.ORDER_CONFIRMATION,
        )

    async def send_order_shipped(self, req: OrderShippedRequest) -> None:
        """Send order-shipped email and optional SMS."""
        try:
            html = self._render(
                "order_shipped.html",
                {
                    "full_name": req.full_name,
                    "order_number": req.order_number,
                    "tracking_number": req.tracking_number,
                    "courier_name": req.courier_name,
                },
            )
        except Exception as exc:
            logger.error("template_render_failed", template="order_shipped.html", error=str(exc))
            return
        await self._send_email(
            to=str(req.to_email),
            subject=f"Your order #{req.order_number} has been shipped!",
            html_body=html,
            notification_type=NotificationType.ORDER_SHIPPED,
        )
        if req.to_phone:
            sms = (
                f"Sabhyakriti: Your order #{req.order_number} has been shipped via "
                f"{req.courier_name}. Track: {req.tracking_number}"
            )
            await self._send_sms(req.to_phone, sms, NotificationType.SMS_ORDER_SHIPPED)

    async def send_order_delivered(self, req: OrderDeliveredRequest) -> None:
        """Send order-delivered email and optional SMS."""
        try:
            html = self._render(
                "order_delivered.html",
                {
                    "full_name": req.full_name,
                    "order_number": req.order_number,
                    "delivered_at": req.delivered_at,
                },
            )
        except Exception as exc:
            logger.error("template_render_failed", template="order_delivered.html", error=str(exc))
            return
        await self._send_email(
            to=str(req.to_email),
            subject=f"Order #{req.order_number} delivered — enjoy your purchase!",
            html_body=html,
            notification_type=NotificationType.ORDER_DELIVERED,
        )
        if req.to_phone:
            sms = (
                f"Sabhyakriti: Order #{req.order_number} has been delivered. "
                "If there's any issue, you can return within 7 days."
            )
            await self._send_sms(req.to_phone, sms, NotificationType.SMS_ORDER_DELIVERED)

    async def send_order_cancelled(self, req: OrderCancelledRequest) -> None:
        """Send order-cancellation confirmation email."""
        try:
            html = self._render(
                "order_cancelled.html",
                {
                    "full_name": req.full_name,
                    "order_number": req.order_number,
                    "reason": req.reason,
                },
            )
        except Exception as exc:
            logger.error("template_render_failed", template="order_cancelled.html", error=str(exc))
            return
        await self._send_email(
            to=str(req.to_email),
            subject=f"Order #{req.order_number} has been cancelled",
            html_body=html,
            notification_type=NotificationType.ORDER_CANCELLED,
        )

    async def send_return_received(self, req: ReturnReceivedRequest) -> None:
        """Send return-received confirmation email."""
        try:
            html = self._render(
                "return_received.html",
                {
                    "full_name": req.full_name,
                    "order_number": req.order_number,
                    "return_id": req.return_id,
                    "items": req.items,
                },
            )
        except Exception as exc:
            logger.error("template_render_failed", template="return_received.html", error=str(exc))
            return
        await self._send_email(
            to=str(req.to_email),
            subject=f"Return #{req.return_id} received — Sabhyakriti",
            html_body=html,
            notification_type=NotificationType.RETURN_RECEIVED,
        )

    async def send_return_approved(self, req: ReturnApprovedRequest) -> None:
        """Send return-approved email with refund amount."""
        try:
            html = self._render(
                "return_approved.html",
                {
                    "full_name": req.full_name,
                    "order_number": req.order_number,
                    "refund_amount": req.refund_amount,
                },
            )
        except Exception as exc:
            logger.error("template_render_failed", template="return_approved.html", error=str(exc))
            return
        await self._send_email(
            to=str(req.to_email),
            subject=f"Your return for order #{req.order_number} has been approved",
            html_body=html,
            notification_type=NotificationType.RETURN_APPROVED,
        )

    async def send_refund_processed(self, req: RefundProcessedRequest) -> None:
        """Send refund-processed confirmation email."""
        try:
            html = self._render(
                "refund_processed.html",
                {
                    "full_name": req.full_name,
                    "order_number": req.order_number,
                    "refund_amount": req.refund_amount,
                },
            )
        except Exception as exc:
            logger.error("template_render_failed", template="refund_processed.html", error=str(exc))
            return
        await self._send_email(
            to=str(req.to_email),
            subject=f"Refund processed for order #{req.order_number}",
            html_body=html,
            notification_type=NotificationType.REFUND_PROCESSED,
        )

    async def send_payment_receipt(self, req: PaymentReceiptRequest) -> None:
        """Send payment-receipt email."""
        try:
            html = self._render(
                "payment_receipt.html",
                {
                    "full_name": req.full_name,
                    "order_number": req.order_number,
                    "payment_id": req.payment_id,
                    "method": req.method,
                    "amount": req.amount,
                    "gst_amount": req.gst_amount,
                    "captured_at": req.captured_at,
                },
            )
        except Exception as exc:
            logger.error("template_render_failed", template="payment_receipt.html", error=str(exc))
            return
        await self._send_email(
            to=str(req.to_email),
            subject=f"Payment receipt for order #{req.order_number}",
            html_body=html,
            notification_type=NotificationType.PAYMENT_RECEIPT,
        )

    # ── SMS Notification Methods ───────────────────────────────────────────────

    async def send_otp_sms(self, req: OTPSMSRequest) -> None:
        """Send an OTP verification code via SMS."""
        message = (
            f"Your Sabhyakriti OTP is {req.otp_code}. "
            "Valid for 10 minutes. Do not share this code with anyone."
        )
        await self._send_sms(req.to_phone, message, NotificationType.SMS_OTP)

    async def send_order_shipped_sms(self, req: OrderShippedSMSRequest) -> None:
        """Send order-shipped SMS."""
        message = (
            f"Sabhyakriti: Your order #{req.order_number} has been shipped via "
            f"{req.courier_name}. Tracking: {req.tracking_number}"
        )
        await self._send_sms(req.to_phone, message, NotificationType.SMS_ORDER_SHIPPED)

    async def send_order_delivered_sms(self, req: OrderDeliveredSMSRequest) -> None:
        """Send order-delivered SMS."""
        message = (
            f"Sabhyakriti: Your order #{req.order_number} has been delivered! "
            "Enjoy your purchase. Returns accepted within 7 days."
        )
        await self._send_sms(req.to_phone, message, NotificationType.SMS_ORDER_DELIVERED)
