# Code Summary — Unit 6: Notification Microservice

55 files generated under `sabhyakriti-notification-service/`.

## Key Highlights
- Internal-only: no public ALB; X-Internal-Secret on all endpoints
- All 13 endpoints return 202 immediately via FastAPI BackgroundTasks (fire-and-forget)
- Every notification method catches ALL exceptions — never propagates to caller
- Twilio (primary, 2 retries) → auto-fallback to AWS SNS on failure
- All send attempts logged to `notification_logs` DB table (SENT or FAILED)
- 10 Jinja2 HTML email templates with brand colours (#FF6B2B saffron, #1B4B5A teal)
- 3 SMS message types as plain text f-strings
- Email sender: "Sabhyakriti" <no-reply@sabhyakriti.com>

## Notification Types
**Email (10)**: email_verification, password_reset, order_confirmation, order_shipped, order_delivered, order_cancelled, return_received, return_approved, refund_processed, payment_receipt
**SMS (3)**: otp_sms, order_shipped_sms, order_delivered_sms

## Tests
- 40+ test cases: all 13 notification types, SENT/FAILED log paths, Twilio→SNS fallover, both-fail silence
- Template rendering tests for all 10 HTML templates with content assertions
