# Business Rules — Unit 5: Payment Microservice

---

## Razorpay Integration Rules

| ID | Rule |
|---|---|
| BR-PAY-001 | Razorpay order created server-side; frontend initialises Razorpay widget using returned `razorpay_order_id` and `razorpay_key_id` |
| BR-PAY-002 | Payment signature verified server-side using HMAC-SHA256: `hmac(key_secret, f"{razorpay_order_id}|{razorpay_payment_id}")` |
| BR-PAY-003 | Payment is NOT captured until signature verification passes — no auto-capture |
| BR-PAY-004 | Razorpay key_id and key_secret loaded from AWS Secrets Manager at startup |
| BR-PAY-005 | Webhook signature verified: `hmac(webhook_secret, raw_body)` == `X-Razorpay-Signature` header |
| BR-PAY-006 | Webhook handler is idempotent: check `WebhookEvent.razorpay_event_id` uniqueness before processing; return 200 silently if duplicate |

## Retry & Auto-Cancel Rules

| ID | Rule |
|---|---|
| BR-PAY-007 | Max 3 payment attempts per order (Q2:A) |
| BR-PAY-008 | Auto-cancel window: 30 minutes from `first_attempt_at` |
| BR-PAY-009 | On each failed payment attempt: increment `attempt_count`; update `last_attempt_at` |
| BR-PAY-010 | If `attempt_count >= 3` OR `NOW() > first_attempt_at + 30min`: Payment.status = CANCELLED; call Order Service to cancel the order; release stock |
| BR-PAY-011 | A new Razorpay order is created for each retry (previous Razorpay order is abandoned) |
| BR-PAY-012 | Background job (APScheduler or Celery-lite) checks for CREATED payments older than 30 minutes and cancels them |

## COD Rules

| ID | Rule |
|---|---|
| BR-PAY-013 | COD available for ALL Indian pincodes — no restriction (Q1:A) |
| BR-PAY-014 | COD orders do not use Razorpay; Payment record created with status=CAPTURED, method=COD immediately |
| BR-PAY-015 | COD payment receipt shows "Payment: Cash on Delivery" |
| BR-PAY-016 | COD refunds are handled manually (admin bank transfer); Payment.status set to REFUNDED by admin action |

## Refund Rules

| ID | Rule |
|---|---|
| BR-PAY-017 | Refunds initiated only by Order Service (internal call) — not directly by customer |
| BR-PAY-018 | Razorpay refund via `razorpay.refund.create(payment_id, amount)` |
| BR-PAY-019 | Partial refund supported (return partial items) |
| BR-PAY-020 | On successful refund API call: store `refund_id`, set `refunded_at`, update Payment.status = REFUNDED |
| BR-PAY-021 | Refund webhook `refund.processed` updates refund status if not already updated via API response |

## Receipt Rules

| ID | Rule |
|---|---|
| BR-PAY-022 | Payment receipt email sent immediately after payment capture (Q3:A) via Notification Service |
| BR-PAY-023 | Receipt includes: order_number, payment_id, method, amount, GST breakdown, captured_at |
| BR-PAY-024 | Receipt stored in DB (Payment record); also retrievable via API for re-download |
