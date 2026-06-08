"""Payment application service — orchestrates all 7 payment flows.

This service is the single entry-point for all business use-cases. It
depends only on abstract repository interfaces and adapter protocols,
keeping it framework-agnostic and trivially testable.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import structlog

from application.clients.notification_service_client import NotificationServiceClient
from application.clients.order_service_client import OrderServiceClient
from application.dtos.payment_dtos import (
    CODConfirmRequest,
    PaymentDTO,
    PaymentReceiptDTO,
    RazorpayOrderDTO,
    RefundDTO,
    RefundRequest,
    VerifyPaymentRequest,
    WebhookEventPayload,
)
from domain.entities.payment import Payment
from domain.repositories.i_payment_repository import IPaymentRepository
from domain.repositories.i_webhook_repository import IWebhookRepository
from domain.services.signature_service import (
    verify_payment_signature,
    verify_webhook_signature,
)
from domain.value_objects import PaymentMethod, PaymentStatus

logger = structlog.get_logger(__name__)

# Business constants
MAX_PAYMENT_ATTEMPTS = 3
PAYMENT_WINDOW_MINUTES = 30
STALE_PAYMENT_CUTOFF_MINUTES = 30


class PaymentApplicationService:
    """Orchestrates all payment use-cases.

    All methods are async; the Razorpay SDK (synchronous) is accessed
    via the injected ``razorpay_adapter`` which wraps calls in a thread pool.
    """

    def __init__(
        self,
        payment_repo: IPaymentRepository,
        webhook_repo: IWebhookRepository,
        razorpay_adapter: "RazorpayAdapterProtocol",  # type: ignore[name-defined]  # noqa: F821
        order_client: OrderServiceClient,
        notification_client: NotificationServiceClient,
        razorpay_key_id: str,
        razorpay_key_secret: str,
        razorpay_webhook_secret: str,
    ) -> None:
        self._payment_repo = payment_repo
        self._webhook_repo = webhook_repo
        self._razorpay = razorpay_adapter
        self._order_client = order_client
        self._notification_client = notification_client
        self._key_id = razorpay_key_id
        self._key_secret = razorpay_key_secret
        self._webhook_secret = razorpay_webhook_secret

    # ------------------------------------------------------------------
    # Flow 1 — Create Razorpay order
    # ------------------------------------------------------------------

    async def create_razorpay_order(
        self,
        order_id: UUID,
        user_id: UUID,
        amount: Decimal,
        currency: str = "INR",
    ) -> RazorpayOrderDTO:
        """Create a Razorpay order and persist a CREATED payment record.

        Enforces the 3-attempt / 30-minute window rate limit.
        """
        log = logger.bind(order_id=str(order_id), user_id=str(user_id))

        existing = await self._payment_repo.get_by_order_id(order_id)
        if existing is not None:
            if existing.status == PaymentStatus.CAPTURED:
                raise ValueError(f"Order {order_id} is already paid.")
            if existing.attempt_count >= MAX_PAYMENT_ATTEMPTS:
                raise ValueError(
                    f"Maximum {MAX_PAYMENT_ATTEMPTS} payment attempts exceeded for order {order_id}."
                )

        amount_paise = int(amount * 100)
        # Razorpay receipt must be <= 40 chars
        receipt = f"ord_{str(order_id).replace('-', '')[-32:]}"

        log.info("creating_razorpay_order", amount_paise=amount_paise)
        rz_order = await self._razorpay.create_order(amount_paise, receipt)

        now = datetime.now(tz=timezone.utc)
        if existing is None:
            payment = Payment(
                payment_id=uuid4(),
                order_id=order_id,
                user_id=user_id,
                amount=amount,
                currency=currency,
                method=PaymentMethod.RAZORPAY,
                status=PaymentStatus.CREATED,
                razorpay_order_id=rz_order["id"],
                attempt_count=1,
                first_attempt_at=now,
                created_at=now,
                updated_at=now,
            )
            await self._payment_repo.create(payment)
        else:
            existing.razorpay_order_id = rz_order["id"]
            existing.attempt_count += 1
            existing.updated_at = now
            await self._payment_repo.update(existing)

        log.info("razorpay_order_created", razorpay_order_id=rz_order["id"])
        return RazorpayOrderDTO(
            razorpay_order_id=rz_order["id"],
            razorpay_key_id=self._key_id,
            amount=amount_paise,
            currency=currency,
            order_id=order_id,
        )

    # ------------------------------------------------------------------
    # Flow 2 — Verify payment after Razorpay callback
    # ------------------------------------------------------------------

    async def verify_payment(self, req: VerifyPaymentRequest) -> PaymentDTO:
        """Verify HMAC-SHA256 signature and capture the payment.

        Raises:
            ValueError: If signature is invalid, payment not found, or
                already captured.
        """
        log = logger.bind(order_id=str(req.order_id))

        payment = await self._payment_repo.get_by_order_id(req.order_id)
        if payment is None:
            raise ValueError(f"No payment found for order {req.order_id}.")

        if payment.status == PaymentStatus.CAPTURED:
            raise ValueError(f"Payment for order {req.order_id} is already captured.")

        if not payment.is_capturable():
            raise ValueError(
                f"Payment for order {req.order_id} cannot be captured in status {payment.status}."
            )

        valid = verify_payment_signature(
            self._key_secret,
            req.razorpay_order_id,
            req.razorpay_payment_id,
            req.razorpay_signature,
        )
        if not valid:
            log.warning("invalid_payment_signature", razorpay_payment_id=req.razorpay_payment_id)
            payment.status = PaymentStatus.FAILED
            payment.updated_at = datetime.now(tz=timezone.utc)
            await self._payment_repo.update(payment)
            raise ValueError("Payment signature verification failed.")

        now = datetime.now(tz=timezone.utc)
        payment.status = PaymentStatus.CAPTURED
        payment.razorpay_payment_id = req.razorpay_payment_id
        payment.razorpay_signature = req.razorpay_signature
        payment.captured_at = now
        payment.updated_at = now
        await self._payment_repo.update(payment)

        log.info("payment_captured", razorpay_payment_id=req.razorpay_payment_id)

        # Notify order service
        await self._order_client.confirm_order(
            req.order_id,
            payment_reference=req.razorpay_payment_id,
            payment_method="RAZORPAY",
        )

        return self._to_dto(payment)

    # ------------------------------------------------------------------
    # Flow 3 — Confirm Cash-on-Delivery payment
    # ------------------------------------------------------------------

    async def confirm_cod_payment(self, req: CODConfirmRequest) -> PaymentDTO:
        """Create a COD payment with CAPTURED status immediately (no Razorpay call)."""
        log = logger.bind(order_id=str(req.order_id))

        existing = await self._payment_repo.get_by_order_id(req.order_id)
        if existing is not None:
            raise ValueError(f"A payment already exists for order {req.order_id}.")

        now = datetime.now(tz=timezone.utc)
        payment = Payment(
            payment_id=uuid4(),
            order_id=req.order_id,
            user_id=req.user_id,
            amount=req.amount,
            currency="INR",
            method=PaymentMethod.COD,
            status=PaymentStatus.CAPTURED,
            attempt_count=1,
            first_attempt_at=now,
            captured_at=now,
            created_at=now,
            updated_at=now,
        )
        await self._payment_repo.create(payment)
        log.info("cod_payment_captured")
        return self._to_dto(payment)

    # ------------------------------------------------------------------
    # Flow 4 — Process Razorpay webhook
    # ------------------------------------------------------------------

    async def process_webhook(
        self,
        raw_body: bytes,
        signature: str,
    ) -> None:
        """Validate and idempotently process an incoming Razorpay webhook.

        Duplicate events (same ``razorpay_event_id``) are silently ignored
        via a UNIQUE constraint on the webhook_events table.
        """
        if not verify_webhook_signature(self._webhook_secret, raw_body, signature):
            raise ValueError("Webhook signature verification failed.")

        body = json.loads(raw_body)
        event_payload = WebhookEventPayload.model_validate(body)

        razorpay_event_id = body.get("id", "")
        if not razorpay_event_id:
            raise ValueError("Webhook body missing 'id' field.")

        log = logger.bind(razorpay_event_id=razorpay_event_id, event=event_payload.event)

        webhook_event, is_new = await self._webhook_repo.create_if_not_exists(
            razorpay_event_id=razorpay_event_id,
            event_type=event_payload.event,
            payload=body,
        )

        if not is_new:
            log.info("webhook_duplicate_ignored")
            return

        try:
            await self._handle_webhook_event(event_payload, log)
            await self._webhook_repo.mark_processed(razorpay_event_id)
        except Exception as exc:
            error_msg = str(exc)
            log.error("webhook_processing_failed", error=error_msg)
            await self._webhook_repo.mark_failed(razorpay_event_id, error_msg)
            raise

    async def _handle_webhook_event(
        self,
        event_payload: WebhookEventPayload,
        log: logging.Logger,  # type: ignore[type-arg]
    ) -> None:
        """Dispatch webhook events to the appropriate handler."""
        event_type = event_payload.event

        if event_type == "payment.captured":
            await self._handle_payment_captured_webhook(event_payload, log)
        elif event_type == "payment.failed":
            await self._handle_payment_failed_webhook(event_payload, log)
        else:
            log.info("webhook_event_unhandled", event=event_type)

    async def _handle_payment_captured_webhook(
        self,
        event_payload: WebhookEventPayload,
        log: logging.Logger,  # type: ignore[type-arg]
    ) -> None:
        """Handle payment.captured event from Razorpay."""
        if event_payload.payload is None or event_payload.payload.payment is None:
            raise ValueError("payment.captured webhook missing payload.payment")

        payment_entity = event_payload.payload.payment.get("entity", {})
        razorpay_payment_id = payment_entity.get("id")
        razorpay_order_id = payment_entity.get("order_id")

        if not razorpay_payment_id or not razorpay_order_id:
            raise ValueError("payment.captured webhook missing payment entity IDs")

        payment = await self._payment_repo.get_by_razorpay_payment_id(razorpay_payment_id)
        if payment is None:
            # Try by razorpay_order_id via a search — here we use get_by_order_id
            # indirectly after looking up by razorpay_payment_id first.
            log.warning(
                "webhook_payment_not_found_by_payment_id",
                razorpay_payment_id=razorpay_payment_id,
            )
            return

        if payment.status == PaymentStatus.CAPTURED:
            log.info("webhook_payment_already_captured")
            return

        now = datetime.now(tz=timezone.utc)
        payment.status = PaymentStatus.CAPTURED
        payment.razorpay_payment_id = razorpay_payment_id
        payment.captured_at = now
        payment.updated_at = now
        await self._payment_repo.update(payment)

        await self._order_client.confirm_order(
            payment.order_id,
            payment_reference=razorpay_payment_id,
            payment_method="RAZORPAY",
        )
        log.info("webhook_payment_captured_processed")

    async def _handle_payment_failed_webhook(
        self,
        event_payload: WebhookEventPayload,
        log: logging.Logger,  # type: ignore[type-arg]
    ) -> None:
        """Handle payment.failed event from Razorpay."""
        if event_payload.payload is None or event_payload.payload.payment is None:
            return

        payment_entity = event_payload.payload.payment.get("entity", {})
        razorpay_payment_id = payment_entity.get("id")
        if not razorpay_payment_id:
            return

        payment = await self._payment_repo.get_by_razorpay_payment_id(razorpay_payment_id)
        if payment is None or payment.status != PaymentStatus.CREATED:
            return

        payment.status = PaymentStatus.FAILED
        payment.updated_at = datetime.now(tz=timezone.utc)
        await self._payment_repo.update(payment)
        log.info("webhook_payment_failed_processed")

    # ------------------------------------------------------------------
    # Flow 5 — Initiate refund (called internally by Order Service)
    # ------------------------------------------------------------------

    async def initiate_refund(self, req: RefundRequest) -> RefundDTO:
        """Initiate a Razorpay refund for a captured payment.

        Raises:
            ValueError: If the payment is not in CAPTURED status or already refunded.
        """
        log = logger.bind(order_id=str(req.order_id))

        payment = await self._payment_repo.get_by_order_id(req.order_id)
        if payment is None:
            raise ValueError(f"No payment found for order {req.order_id}.")
        if not payment.is_refundable():
            raise ValueError(
                f"Payment for order {req.order_id} is not refundable (status: {payment.status})."
            )
        if payment.razorpay_payment_id is None:
            raise ValueError(f"Payment for order {req.order_id} has no Razorpay payment ID.")

        amount_paise = int(req.amount * 100)
        log.info("initiating_refund", amount_paise=amount_paise)

        refund = await self._razorpay.create_refund(payment.razorpay_payment_id, amount_paise)

        now = datetime.now(tz=timezone.utc)
        payment.status = PaymentStatus.REFUNDED
        payment.refund_id = refund["id"]
        payment.refund_amount = req.amount
        payment.refunded_at = now
        payment.updated_at = now
        await self._payment_repo.update(payment)

        log.info("refund_created", refund_id=refund["id"])
        return RefundDTO(
            refund_id=refund["id"],
            order_id=req.order_id,
            amount=req.amount,
            status=refund.get("status", "created"),
            created_at=now,
        )

    # ------------------------------------------------------------------
    # Flow 6 — Get payment receipt
    # ------------------------------------------------------------------

    async def get_payment_receipt(
        self,
        user_id: UUID,
        order_id: UUID,
    ) -> PaymentReceiptDTO:
        """Return a payment receipt for the given order.

        Performs an IDOR check: the requesting user must own the order.

        Raises:
            ValueError: If payment not found, not captured, or IDOR detected.
        """
        payment = await self._payment_repo.get_by_order_id(order_id)
        if payment is None:
            raise ValueError(f"No payment found for order {order_id}.")

        if payment.user_id != user_id:
            raise PermissionError(f"User {user_id} does not own order {order_id}.")

        if payment.status != PaymentStatus.CAPTURED:
            raise ValueError(f"Payment for order {order_id} is not yet captured.")

        if payment.captured_at is None:
            raise ValueError(f"Payment for order {order_id} has no captured_at timestamp.")

        order_number = await self._order_client.get_order_number(order_id)

        return PaymentReceiptDTO(
            order_id=order_id,
            order_number=order_number,
            payment_id=payment.payment_id,
            razorpay_payment_id=payment.razorpay_payment_id,
            method=payment.method,
            amount=payment.amount,
            captured_at=payment.captured_at,
            status=payment.status,
        )

    # ------------------------------------------------------------------
    # Flow 7 — Cancel stale payments (APScheduler background job)
    # ------------------------------------------------------------------

    async def cancel_stale_payments(self) -> int:
        """Cancel all CREATED payments older than PAYMENT_WINDOW_MINUTES.

        This is invoked every 5 minutes by APScheduler.

        Returns:
            Number of payments cancelled.
        """
        cutoff = datetime.now(tz=timezone.utc) - timedelta(minutes=STALE_PAYMENT_CUTOFF_MINUTES)
        stale_payments = await self._payment_repo.list_stale_created(cutoff)

        cancelled = 0
        for payment in stale_payments:
            log = logger.bind(payment_id=str(payment.payment_id), order_id=str(payment.order_id))
            try:
                payment.status = PaymentStatus.CANCELLED
                payment.updated_at = datetime.now(tz=timezone.utc)
                await self._payment_repo.update(payment)
                await self._order_client.cancel_order(
                    payment.order_id,
                    reason="Payment window expired (30 minutes)",
                )
                cancelled += 1
                log.info("stale_payment_cancelled")
            except Exception as exc:
                log.error("stale_payment_cancel_failed", error=str(exc))

        if cancelled > 0:
            logger.info("stale_payments_cancelled", count=cancelled)
        return cancelled

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    @staticmethod
    def _to_dto(payment: Payment) -> PaymentDTO:
        return PaymentDTO(
            payment_id=payment.payment_id,
            order_id=payment.order_id,
            status=payment.status,
            method=payment.method,
            amount=payment.amount,
            razorpay_payment_id=payment.razorpay_payment_id,
            captured_at=payment.captured_at,
            refund_id=payment.refund_id,
            refund_amount=payment.refund_amount,
            refunded_at=payment.refunded_at,
        )
