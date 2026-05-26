# Domain Entities — Unit 6: Notification Microservice

## Entity: NotificationLog

| Field | Type | Constraints | Description |
|---|---|---|---|
| `log_id` | UUID | PK | |
| `notification_type` | VARCHAR(50) | NOT NULL | e.g., `order_confirmation`, `otp_sms` |
| `channel` | VARCHAR(10) | NOT NULL | `EMAIL` or `SMS` |
| `recipient` | VARCHAR(255) | NOT NULL | Email address or phone number |
| `status` | VARCHAR(10) | NOT NULL | `SENT` or `FAILED` |
| `provider` | VARCHAR(20) | nullable | `SES`, `TWILIO`, `SNS` — which provider actually sent |
| `error_message` | TEXT | nullable | Set on FAILED |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Indexes**: `notification_type`, `recipient`, `status`, `created_at DESC`

## Value Objects

| Value Object | Values |
|---|---|
| `NotificationChannel` | `EMAIL`, `SMS` |
| `NotificationStatus` | `SENT`, `FAILED` |
| `NotificationType` | `email_verification`, `password_reset`, `order_confirmation`, `order_shipped`, `order_delivered`, `order_cancelled`, `return_received`, `return_approved`, `refund_processed`, `payment_receipt`, `otp_sms`, `order_shipped_sms`, `order_delivered_sms` |

## Email Templates (Jinja2 HTML)

| Template File | Notification Type | Key Variables |
|---|---|---|
| `email_verification.html` | email_verification | full_name, verification_link, expiry_hours=48 |
| `password_reset.html` | password_reset | full_name, reset_link, expiry_hours=2 |
| `order_confirmation.html` | order_confirmation | full_name, order_number, items[], subtotal, gst, total, shipping_address, payment_method |
| `order_shipped.html` | order_shipped | full_name, order_number, tracking_number, courier_name, tracking_url |
| `order_delivered.html` | order_delivered | full_name, order_number, delivered_at, return_window_days=7 |
| `order_cancelled.html` | order_cancelled | full_name, order_number, cancellation_reason |
| `return_received.html` | return_received | full_name, order_number, return_id, items[] |
| `return_approved.html` | return_approved | full_name, order_number, refund_amount, refund_days=5 |
| `refund_processed.html` | refund_processed | full_name, order_number, refund_amount, refund_days=5 |
| `payment_receipt.html` | payment_receipt | full_name, order_number, payment_id, method, amount, gst_amount, captured_at |

## SMS Messages (plain text f-strings)

| Type | Message Template |
|---|---|
| `otp_sms` | `Your Sabhyakriti OTP is {otp_code}. Valid for 10 minutes. Do not share.` |
| `order_shipped_sms` | `Your Sabhyakriti order #{order_number} has been shipped via {courier}. Track: {tracking_number}` |
| `order_delivered_sms` | `Your Sabhyakriti order #{order_number} has been delivered. Enjoy! Return within 7 days if needed.` |
