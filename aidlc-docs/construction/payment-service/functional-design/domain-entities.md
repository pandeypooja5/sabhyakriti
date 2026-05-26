# Domain Entities — Unit 5: Payment Microservice

---

## Entity: Payment

| Field | Type | Constraints | Description |
|---|---|---|---|
| `payment_id` | UUID | PK | |
| `order_id` | UUID | UNIQUE, NOT NULL | One payment record per order |
| `razorpay_order_id` | VARCHAR(100) | UNIQUE, nullable | Razorpay order ID (null for COD) |
| `razorpay_payment_id` | VARCHAR(100) | UNIQUE, nullable | Set after successful capture |
| `razorpay_signature` | VARCHAR(200) | nullable | HMAC stored for audit |
| `status` | VARCHAR(20) | NOT NULL | See PaymentStatus enum |
| `method` | VARCHAR(20) | NOT NULL | `RAZORPAY`, `UPI`, `COD` |
| `amount` | NUMERIC(10,2) | NOT NULL | Total amount in INR |
| `attempt_count` | SMALLINT | NOT NULL, DEFAULT 0 | Incremented on each frontend payment attempt |
| `first_attempt_at` | TIMESTAMPTZ | nullable | Time of first payment attempt |
| `last_attempt_at` | TIMESTAMPTZ | nullable | Time of most recent attempt |
| `captured_at` | TIMESTAMPTZ | nullable | Time payment was captured |
| `refund_id` | VARCHAR(100) | nullable | Razorpay refund ID after refund |
| `refunded_at` | TIMESTAMPTZ | nullable | |
| `refund_amount` | NUMERIC(10,2) | nullable | May be partial |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Indexes**: `order_id` (unique), `razorpay_order_id` (unique), `razorpay_payment_id` (unique), `status`

---

## Entity: WebhookEvent

| Field | Type | Constraints | Description |
|---|---|---|---|
| `event_id` | UUID | PK | |
| `razorpay_event_id` | VARCHAR(100) | UNIQUE, NOT NULL | Razorpay `event.id` — uniqueness prevents duplicate processing |
| `event_type` | VARCHAR(100) | NOT NULL | e.g., `payment.captured`, `refund.created` |
| `payload` | JSONB | NOT NULL | Full webhook payload for audit |
| `processed` | BOOLEAN | NOT NULL, DEFAULT FALSE | Set TRUE after successful processing |
| `error_message` | TEXT | nullable | Set if processing failed |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | When webhook was received |
| `processed_at` | TIMESTAMPTZ | nullable | When processing completed |

**Indexes**: `razorpay_event_id` (unique — idempotency key), `event_type`, `processed`

---

## Value Objects

| Value Object | Values |
|---|---|
| `PaymentStatus` | `CREATED` → `CAPTURED`; branches: `FAILED`, `CANCELLED`, `REFUNDED` |
| `PaymentMethod` | `RAZORPAY`, `UPI`, `COD` |
| `WebhookEventType` | `payment.captured`, `payment.failed`, `refund.created`, `refund.processed`, `payment.authorized` |
