# Functional Design Plan — Unit 5: Payment Microservice
# sabhyakriti-payment-service

---

## Execution Checklist

- [x] Step 1: Answers — Q1:A (COD all pincodes) Q2:A (3 attempts/30min) Q3:A (auto receipt email)
- [x] Step 2: Analyze answers — NO ambiguities detected
- [x] Step 3: Generate domain-entities.md
- [x] Step 4: Generate business-rules.md
- [x] Step 5: Generate business-logic-model.md
- [x] Step 6: Present for approval

---

## Context Summary

Unit 5 owns: Payment entity and WebhookEvent log.
Handles: Razorpay order creation, HMAC-SHA256 payment verification, COD confirmation,
Razorpay webhook processing (idempotent), refund initiation, payment receipt.
Requirements: FR-PAY-01 to FR-PAY-07.

Most payment design is already determined:
- Razorpay SDK for card/net banking/UPI
- HMAC-SHA256 signature verification server-side
- Idempotent webhook handler
- Payment receipt stored in DB + emailed

Genuinely open decisions below:

---

## Business Logic Questions

Please fill in the letter choice after each `[Answer]:` tag and let me know when done.

---

## Question 1
For COD orders — is Cash on Delivery available for ALL pincodes, or only a specific set?

A) COD available for ALL Indian pincodes — no restriction
B) COD available only for major metro cities (Delhi, Mumbai, Bengaluru, Chennai, Hyderabad, Kolkata, Pune, Ahmedabad) — ~500 pincodes
C) COD available everywhere EXCEPT J&K, Andaman & Nicobar, Lakshadweep, and remote NE states — based on a blocklist
D) Other (please describe after [Answer]: tag below)

[Answer]: 

---

## Question 2
If a Razorpay/UPI payment fails (e.g., bank declines) — how many retry attempts should be allowed before the order is automatically cancelled?

A) 3 attempts — user can retry 3 times within 30 minutes; order auto-cancelled after that
B) 5 attempts — more lenient; 30-minute window
C) No auto-cancel — user can retry indefinitely until they cancel or complete payment
D) Other (please describe after [Answer]: tag below)

[Answer]: 

---

## Question 3
Should a payment receipt be emailed to the customer automatically after successful payment?

A) Yes — send payment receipt email via Notification Service immediately after payment capture
B) No — receipt only available via "Download Invoice" on the order detail page; no auto-email
C) Other (please describe after [Answer]: tag below)

[Answer]: 
