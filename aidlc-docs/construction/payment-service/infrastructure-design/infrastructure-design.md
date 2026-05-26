# Infrastructure Design — Unit 5: Payment Microservice

## AWS Mapping
| Component | AWS Service | Config |
|---|---|---|
| Compute | EC2 t3.medium | Private subnet; Docker; port 8005 |
| Load balancer | ALB (shared) | `/api/v1/payments/*` → port 8005 |
| Webhook endpoint | ALB | `/api/v1/payments/webhook` — public, Razorpay IPs allowlisted at ALB level |
| DB | RDS PostgreSQL primary | `payment` schema |
| Secrets | AWS Secrets Manager | `sabhyakriti/payment/razorpay-key-id`, `sabhyakriti/payment/razorpay-key-secret`, `sabhyakriti/payment/razorpay-webhook-secret` |
| Logs | CloudWatch `/sabhyakriti/payment-service` | 90 days |
| Container | ECR `sabhyakriti/payment-service` | |

## Database Schema (payment)

```sql
CREATE SCHEMA IF NOT EXISTS payment;

CREATE TABLE payment.payments (
    payment_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id             UUID NOT NULL UNIQUE,
    razorpay_order_id    VARCHAR(100) UNIQUE,
    razorpay_payment_id  VARCHAR(100) UNIQUE,
    razorpay_signature   VARCHAR(200),
    status               VARCHAR(20) NOT NULL DEFAULT 'CREATED',
    method               VARCHAR(20) NOT NULL,
    amount               NUMERIC(10,2) NOT NULL,
    attempt_count        SMALLINT NOT NULL DEFAULT 0,
    first_attempt_at     TIMESTAMPTZ,
    last_attempt_at      TIMESTAMPTZ,
    captured_at          TIMESTAMPTZ,
    refund_id            VARCHAR(100),
    refunded_at          TIMESTAMPTZ,
    refund_amount        NUMERIC(10,2),
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE payment.webhook_events (
    event_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    razorpay_event_id  VARCHAR(100) NOT NULL UNIQUE,
    event_type         VARCHAR(100) NOT NULL,
    payload            JSONB NOT NULL,
    processed          BOOLEAN NOT NULL DEFAULT FALSE,
    error_message      TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at       TIMESTAMPTZ
);

CREATE INDEX idx_payments_order ON payment.payments(order_id);
CREATE INDEX idx_payments_status ON payment.payments(status);
CREATE INDEX idx_payments_created ON payment.payments(created_at);
CREATE INDEX idx_webhook_event_id ON payment.webhook_events(razorpay_event_id);
CREATE INDEX idx_webhook_processed ON payment.webhook_events(processed);
```
