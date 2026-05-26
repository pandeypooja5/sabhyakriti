# NFR Requirements — Unit 5: Payment Microservice

## Performance
- Create Razorpay order p95: < 600ms (Razorpay API call included)
- Verify payment p95: < 300ms (HMAC local, then async Order Service call)
- Webhook processing p95: < 200ms (DB idempotency check + status update)
- All other endpoints p95: < 500ms

## Security (Critical — payment service)
- All 15 SECURITY rules enforced
- Razorpay key_secret NEVER logged or returned in responses
- Webhook raw body preserved as bytes for HMAC verification before JSON parsing
- Payment amounts validated against Order Service (prevent tampering)
- Internal endpoints require shared-secret header
- SECURITY-11: rate limiting on verify endpoint (10 req/min per IP)

## Scalability
- EC2 t3.medium; APScheduler running in-process for auto-cancel job
- No Redis needed (no caching)

## Testing
- 80% line coverage
- PBT: HMAC signature generation/verification (property: verify(sign(x)) == True always)
- Webhook idempotency test: same event_id twice → processed only once
- Signature tamper test: wrong signature → always 400
