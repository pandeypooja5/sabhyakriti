# Functional Design Plan — Unit 6: Notification Microservice
# sabhyakriti-notification-service

---

## Execution Checklist

- [x] Step 1: Answers — Q1:A (Twilio→SNS fallback) Q2:A (DB log) Q3:A (Sabhyakriti no-reply@)
- [x] Step 2: Analyze answers — NO ambiguities
- [ ] Step 3: Generate artifacts + code
- [ ] Step 4: Present for approval

---

## Context Summary

Unit 6 is internal-only (not exposed via public ALB).
Handles: all transactional emails (AWS SES) + SMS (Twilio primary, SNS fallback).
Notification types: email_verification, password_reset, order_confirmation, order_shipped,
order_delivered, order_cancelled, return_received, return_approved, refund_processed,
payment_receipt, otp_sms, order_shipped_sms, order_delivered_sms.
All sends are fire-and-forget; callers do not wait for delivery confirmation.

---

## Business Logic Questions

Please fill in the letter choice after each `[Answer]:` tag and let me know when done.

---

## Question 1
If Twilio SMS fails (all retries exhausted), should it automatically fallback to AWS SNS?

A) Yes — try Twilio first (2 retries), then automatically fallback to SNS if Twilio fails
B) No — log the failure and give up; no SNS fallback (simpler, SNS requires additional setup)
C) Other (please describe after [Answer]: tag below)

[Answer]: 

---

## Question 2
Should notification send attempts be logged to the database (for debugging/audit)?

A) Yes — log each send attempt (notification type, recipient, channel, status, error) to a `notification_logs` table
B) No — log to CloudWatch only; no separate DB table needed
C) Other (please describe after [Answer]: tag below)

[Answer]: 

---

## Question 3
What email display name and address should be used as the sender?

A) "Sabhyakriti" <no-reply@sabhyakriti.com> — clean brand name
B) "Sabhyakriti Store" <orders@sabhyakriti.com> — more specific
C) Other (please describe after [Answer]: tag below)

[Answer]: 
