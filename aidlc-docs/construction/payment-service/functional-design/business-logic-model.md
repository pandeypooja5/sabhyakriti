# Business Logic Model — Unit 5: Payment Microservice

---

## Flow 1: Create Razorpay Order

```
Input: order_id, amount (from Order Service or frontend POST)

1. Load Payment by order_id — if already CAPTURED: return 409 "Already paid"
2. Call Razorpay API: razorpay.order.create({amount: amount*100, currency: "INR", receipt: order_id})
3. Create/update Payment {razorpay_order_id, status=CREATED, method=RAZORPAY, amount}
4. Return RazorpayOrderDTO {razorpay_order_id, razorpay_key_id, amount, currency, order_id}
   (frontend uses these to open Razorpay checkout widget)
```

---

## Flow 2: Verify Payment (Frontend Callback)

```
Input: order_id, razorpay_payment_id, razorpay_order_id, razorpay_signature

1. Load Payment by order_id → 404 if not found
2. Check status != CAPTURED → 409 if already captured (idempotent)
3. Verify HMAC-SHA256 signature (BR-PAY-002):
   expected = hmac_sha256(key_secret, f"{razorpay_order_id}|{razorpay_payment_id}")
   IF expected != razorpay_signature → 400 "Payment verification failed" (log attempt)
4. Update Payment {razorpay_payment_id, razorpay_signature, status=CAPTURED, captured_at=NOW()}
5. Call Order Service: POST /internal/v1/orders/{order_id}/confirm (async-safe, with retry)
6. Call Notification Service: send_payment_receipt (background task)
7. Return PaymentDTO
```

---

## Flow 3: Handle COD Confirmation

```
Input: order_id, amount (called internally after Order Service creates COD order)

1. Create Payment {order_id, method=COD, status=CAPTURED, amount, captured_at=NOW()}
2. Call Notification Service: send_payment_receipt (background task)
3. Return PaymentDTO
```

---

## Flow 4: Process Razorpay Webhook (Idempotent)

```
Input: raw_body (bytes), X-Razorpay-Signature header

1. Verify webhook signature: hmac_sha256(webhook_secret, raw_body) == header value → 400 if mismatch
2. Parse payload → extract razorpay_event_id and event_type
3. INSERT INTO webhook_events (razorpay_event_id, event_type, payload) ON CONFLICT DO NOTHING
   IF 0 rows inserted (duplicate): return 200 immediately (idempotent)
4. Route by event_type:
   payment.captured:
     Load Payment by razorpay_payment_id; if not CAPTURED: update to CAPTURED; confirm order
   payment.failed:
     Load Payment; increment attempt_count; check auto-cancel condition (BR-PAY-010)
   refund.created / refund.processed:
     Update Payment {refund_id, refunded_at, status=REFUNDED}; update WebhookEvent.processed=True
5. Mark WebhookEvent.processed = True, processed_at = NOW()
6. Return 200 OK (always — Razorpay will retry if non-200)
```

---

## Flow 5: Initiate Refund (called by Order Service)

```
Input: order_id, amount (partial or full)

1. Load Payment by order_id → 404 if not found
2. Validate status = CAPTURED → 400 if not (cannot refund uncaptured payment)
3. Validate amount ≤ Payment.amount → 400 if exceeds
4. IF method = COD: update Payment.status = REFUNDED (manual refund, no API call); notify
5. IF method in (RAZORPAY, UPI):
   Call Razorpay: razorpay.refund.create(razorpay_payment_id, {amount: amount*100})
   Update Payment {refund_id, refund_amount, refunded_at, status=REFUNDED}
6. Call Notification Service: send_refund_processed(order_id, amount) (background)
7. Return RefundDTO {refund_id, amount, status}
```

---

## Flow 6: Get Payment Receipt

```
Input: user_id, order_id

1. Validate user owns order (call Order Service GET /internal/v1/orders/{order_id}/user-check)
2. Load Payment by order_id → 404 if not found
3. Return PaymentReceiptDTO {order_number, payment_id, razorpay_payment_id, method, amount, gst_amount, captured_at, status}
```

---

## Flow 7: Background Auto-Cancel Stale Payments

```
Runs every 5 minutes via APScheduler

1. SELECT payments WHERE status = 'CREATED' AND first_attempt_at < NOW() - INTERVAL '30 minutes'
2. For each stale payment:
   a. Update Payment.status = CANCELLED
   b. Call Order Service: POST /internal/v1/orders/{order_id}/cancel (auto-cancel)
   c. Log cancellation
```

---

## Error Response Standards

| Scenario | HTTP | Message |
|---|---|---|
| Already paid | 409 | "Payment already captured for this order." |
| Signature mismatch | 400 | "Payment verification failed." |
| Payment not found | 404 | "No payment record found for this order." |
| Refund exceeds amount | 400 | "Refund amount exceeds payment amount." |
| Cannot refund | 400 | "Payment must be captured before refund." |
