# Infrastructure Design — Unit 4: Order Microservice

## AWS Mapping

| Component | AWS Service | Config |
|---|---|---|
| Compute | EC2 t3.medium | Private subnet; Docker; port 8004 |
| Load balancer | ALB shared | `/api/v1/orders/*`, `/api/v1/addresses/*` → port 8004 |
| DB primary | RDS PostgreSQL 15 | `order` schema; writes |
| DB replica | RDS read replica | list_orders, get_order_detail reads |
| Logs | CloudWatch `/sabhyakriti/order-service` | 90 days |
| Container | ECR `sabhyakriti/order-service` | |

## Database Schema (order)

```sql
CREATE SCHEMA IF NOT EXISTS "order";

CREATE SEQUENCE "order".order_seq START 1 INCREMENT 1;

CREATE TABLE "order".orders (
    order_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number     VARCHAR(30) NOT NULL UNIQUE,
    user_id          UUID NOT NULL,
    status           VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    payment_method   VARCHAR(20) NOT NULL,
    subtotal         NUMERIC(10,2) NOT NULL,
    discount_amount  NUMERIC(10,2) NOT NULL DEFAULT 0,
    gst_amount       NUMERIC(10,2) NOT NULL,
    shipping_charge  NUMERIC(10,2) NOT NULL DEFAULT 0,
    total_amount     NUMERIC(10,2) NOT NULL,
    coupon_code_used VARCHAR(50),
    shipping_address JSONB NOT NULL,
    tracking_number  VARCHAR(100),
    courier_name     VARCHAR(100),
    notes            TEXT,
    placed_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    confirmed_at     TIMESTAMPTZ,
    shipped_at       TIMESTAMPTZ,
    delivered_at     TIMESTAMPTZ,
    cancelled_at     TIMESTAMPTZ,
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE "order".order_items (
    order_item_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id         UUID NOT NULL REFERENCES "order".orders(order_id) ON DELETE CASCADE,
    product_id       UUID NOT NULL,
    product_name     VARCHAR(200) NOT NULL,
    product_image_url VARCHAR(600),
    quantity         SMALLINT NOT NULL CHECK (quantity >= 1),
    unit_price       NUMERIC(10,2) NOT NULL,
    discounted_price NUMERIC(10,2) NOT NULL,
    item_total       NUMERIC(10,2) NOT NULL
);

CREATE TABLE "order".addresses (
    address_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL,
    full_name    VARCHAR(100) NOT NULL,
    phone        VARCHAR(15) NOT NULL,
    address_line1 VARCHAR(200) NOT NULL,
    address_line2 VARCHAR(200),
    city         VARCHAR(100) NOT NULL,
    state        VARCHAR(100) NOT NULL,
    pincode      VARCHAR(10) NOT NULL CHECK (pincode ~ '^\d{6}$'),
    is_default   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE "order".return_requests (
    return_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id       UUID NOT NULL UNIQUE REFERENCES "order".orders(order_id),
    user_id        UUID NOT NULL,
    status         VARCHAR(30) NOT NULL DEFAULT 'PENDING_REVIEW',
    reason         VARCHAR(500) NOT NULL,
    admin_notes    TEXT,
    refund_amount  NUMERIC(10,2),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE "order".return_items (
    return_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    return_id      UUID NOT NULL REFERENCES "order".return_requests(return_id) ON DELETE CASCADE,
    order_item_id  UUID NOT NULL REFERENCES "order".order_items(order_item_id),
    quantity       SMALLINT NOT NULL CHECK (quantity >= 1),
    reason         VARCHAR(200)
);

-- Indexes
CREATE INDEX idx_orders_user ON "order".orders(user_id);
CREATE INDEX idx_orders_status ON "order".orders(status);
CREATE INDEX idx_orders_placed ON "order".orders(placed_at DESC);
CREATE INDEX idx_order_items_order ON "order".order_items(order_id);
CREATE INDEX idx_addresses_user ON "order".addresses(user_id);
CREATE UNIQUE INDEX idx_addresses_default ON "order".addresses(user_id) WHERE is_default = TRUE;
CREATE INDEX idx_returns_order ON "order".return_requests(order_id);
```

## Internal Endpoints (not on public ALB)
- `POST /internal/v1/orders/{order_id}/confirm` — called by Payment Service
- `GET /internal/v1/orders/verified-purchase` — called by Product Service (review eligibility)
- All require `X-Internal-Secret` header
