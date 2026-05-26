# Code Summary — Unit 5: Payment Microservice

54 files generated under `sabhyakriti-payment-service/`.

## Key Highlights
- HMAC-SHA256 payment signature verification (constant-time via `hmac.compare_digest`)
- Webhook idempotency: INSERT ON CONFLICT DO NOTHING prevents duplicate processing
- Razorpay SDK is synchronous — wrapped in `run_in_executor` for async compatibility
- APScheduler: runs `cancel_stale_payments()` every 5 minutes in-process
- COD flow: Payment created as CAPTURED immediately, no Razorpay API call
- Max 3 attempts / 30-minute auto-cancel window
- All Razorpay credentials from AWS Secrets Manager (3 secrets loaded concurrently at startup)
- Payment receipt email sent after CAPTURED (fire-and-forget background task)
- Internal refund endpoint called by Order Service only (shared-secret protected)

## Tests
- Hypothesis PBT: sign+verify roundtrip invariant, tampered signature always False, wrong key always False
- Webhook idempotency: Order Service confirm called exactly once across N duplicate deliveries
- All 7 flows covered with mocked adapters
