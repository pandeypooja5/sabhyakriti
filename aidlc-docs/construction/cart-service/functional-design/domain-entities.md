# Domain Entities — Unit 3: Cart & Wishlist Microservice

---

## Entity: Cart

| Field | Type | Constraints | Description |
|---|---|---|---|
| `cart_id` | UUID | PK | Auto-generated |
| `user_id` | UUID | UNIQUE, NOT NULL | One cart per user (one-to-one) |
| `applied_coupon_code` | VARCHAR(50) | nullable | Currently applied coupon code (NULL = no coupon) |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Auto-updated on any cart change |

**Indexes**: `user_id` (unique)

**Note**: Cart never expires (persists indefinitely per Q3). `updated_at` tracked for analytics only.

---

## Entity: CartItem

| Field | Type | Constraints | Description |
|---|---|---|---|
| `cart_item_id` | UUID | PK | |
| `cart_id` | UUID | FK → Cart, NOT NULL | |
| `product_id` | UUID | NOT NULL | Reference to Product Service product |
| `quantity` | SMALLINT | NOT NULL, ≥ 1 | |
| `added_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Constraints**: UNIQUE `(cart_id, product_id)` — one CartItem row per product per cart (update quantity instead of inserting duplicate)

**Indexes**: `cart_id`, `(cart_id, product_id)` unique

---

## Entity: Wishlist

| Field | Type | Constraints | Description |
|---|---|---|---|
| `wishlist_id` | UUID | PK | |
| `user_id` | UUID | UNIQUE, NOT NULL | One wishlist per user |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Indexes**: `user_id` (unique)

---

## Entity: WishlistItem

| Field | Type | Constraints | Description |
|---|---|---|---|
| `wishlist_item_id` | UUID | PK | |
| `wishlist_id` | UUID | FK → Wishlist, NOT NULL | |
| `product_id` | UUID | NOT NULL | Reference to Product Service product |
| `added_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Constraints**: UNIQUE `(wishlist_id, product_id)` — idempotent add

**Indexes**: `wishlist_id`, `(wishlist_id, product_id)` unique

---

## Entity: Coupon

| Field | Type | Constraints | Description |
|---|---|---|---|
| `coupon_id` | UUID | PK | |
| `code` | VARCHAR(50) | UNIQUE, NOT NULL | Case-insensitive lookup; stored UPPERCASE |
| `type` | VARCHAR(10) | NOT NULL | Enum: `FLAT` or `PERCENT` |
| `value` | NUMERIC(10,2) | NOT NULL, > 0 | ₹ amount (FLAT) or percentage 0–100 (PERCENT) |
| `min_order_amount` | NUMERIC(10,2) | NOT NULL, DEFAULT 0 | Minimum cart subtotal to apply |
| `max_uses` | INTEGER | nullable | NULL = unlimited uses |
| `used_count` | INTEGER | NOT NULL, DEFAULT 0 | Incremented on each successful order |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | |
| `expires_at` | TIMESTAMPTZ | nullable | NULL = never expires |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Indexes**: `code` (unique), `is_active` (partial WHERE is_active = TRUE)

---

## Value Objects

| Value Object | Type | Values |
|---|---|---|
| `CouponType` | Enum | `FLAT`, `PERCENT` |
| `CartTotals` | VO | `subtotal`, `discount_amount`, `gst_amount`, `shipping_charge`, `total` — all Decimal(10,2) |

---

## CartTotals Computation (Value Object)

```
subtotal         = SUM(item.quantity × item.discounted_price)   [fetched from Product Service]
discount_amount  = coupon_discount(subtotal, coupon)             [0 if no coupon]
taxable_amount   = subtotal - discount_amount
gst_amount       = ROUND(taxable_amount × 0.05, 2)              [5% GST on sarees, separate line item]
shipping_charge  = 0.00                                          [free shipping always — Q1:A]
total            = taxable_amount + gst_amount + shipping_charge

coupon_discount logic:
  FLAT:    discount_amount = MIN(coupon.value, subtotal)           [cannot exceed subtotal]
  PERCENT: discount_amount = ROUND(subtotal × coupon.value/100, 2) [no cap — Q5:C]
```
