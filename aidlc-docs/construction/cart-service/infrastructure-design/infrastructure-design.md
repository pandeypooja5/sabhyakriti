# Infrastructure Design — Unit 3: Cart & Wishlist Microservice

## AWS Service Mapping

| Component | AWS Service | Config |
|---|---|---|
| Compute | EC2 t3.medium | Private subnet; Docker; port 8003 |
| Load balancer | ALB (shared) | `/api/v1/cart/*`, `/api/v1/wishlist/*`, `/api/v1/coupons/*` → port 8003 |
| Database | RDS PostgreSQL primary | `cart` schema; `db.t3.micro` |
| Logs | CloudWatch `/sabhyakriti/cart-service` | 90 days |
| Container | ECR `sabhyakriti/cart-service` | |

## Database Schema (cart)

```sql
CREATE SCHEMA IF NOT EXISTS cart;

CREATE TABLE cart.carts (
    cart_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL UNIQUE,
    applied_coupon_code VARCHAR(50),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE cart.cart_items (
    cart_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cart_id      UUID NOT NULL REFERENCES cart.carts(cart_id) ON DELETE CASCADE,
    product_id   UUID NOT NULL,
    quantity     SMALLINT NOT NULL CHECK (quantity >= 1 AND quantity <= 10),
    added_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (cart_id, product_id)
);

CREATE TABLE cart.wishlists (
    wishlist_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE cart.wishlist_items (
    wishlist_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wishlist_id      UUID NOT NULL REFERENCES cart.wishlists(wishlist_id) ON DELETE CASCADE,
    product_id       UUID NOT NULL,
    added_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (wishlist_id, product_id)
);

CREATE TABLE cart.coupons (
    coupon_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code             VARCHAR(50) NOT NULL UNIQUE,
    type             VARCHAR(10) NOT NULL CHECK (type IN ('FLAT','PERCENT')),
    value            NUMERIC(10,2) NOT NULL CHECK (value > 0),
    min_order_amount NUMERIC(10,2) NOT NULL DEFAULT 0,
    max_uses         INTEGER,
    used_count       INTEGER NOT NULL DEFAULT 0,
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at       TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cart_user ON cart.carts(user_id);
CREATE INDEX idx_cart_items_cart ON cart.cart_items(cart_id);
CREATE INDEX idx_wishlist_user ON cart.wishlists(user_id);
CREATE INDEX idx_wishlist_items_wishlist ON cart.wishlist_items(wishlist_id);
CREATE INDEX idx_coupon_code ON cart.coupons(code);
CREATE INDEX idx_coupon_active ON cart.coupons(is_active) WHERE is_active = TRUE;
```
