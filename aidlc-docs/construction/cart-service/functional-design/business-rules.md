# Business Rules — Unit 3: Cart & Wishlist Microservice

---

## Cart Rules

| ID | Rule |
|---|---|
| BR-CART-001 | One cart per authenticated user; created automatically on first add-to-cart |
| BR-CART-002 | Cart persists indefinitely — no expiry |
| BR-CART-003 | One CartItem row per product per cart; adding the same product again increments quantity |
| BR-CART-004 | Cart is cleared (all items deleted) after the Order Service creates an order from it |
| BR-CART-005 | Maximum 20 distinct products in a single cart; adding a 21st returns HTTP 400 |
| BR-CART-006 | Maximum quantity per item: 10; attempting to set quantity > 10 returns HTTP 400 |
| BR-CART-007 | Setting quantity to 0 removes the item (equivalent to remove endpoint) |
| BR-CART-008 | If a product is out of stock (`stock_qty = 0`) when cart totals are calculated, item is flagged `is_available: false` in CartItemDTO — item stays in cart but user is warned |
| BR-CART-009 | Cart pricing always fetches live `discounted_price` from Product Service at calculation time — prices are never cached in cart |

---

## Coupon Rules

| ID | Rule |
|---|---|
| BR-CART-010 | Only one coupon can be applied at a time (Q4:A); applying a new code replaces the existing one |
| BR-CART-011 | Coupon code lookup is case-insensitive; stored and compared as UPPERCASE |
| BR-CART-012 | Coupon must be active (`is_active = TRUE`) |
| BR-CART-013 | Coupon must not be expired (`expires_at IS NULL OR expires_at > NOW()`) |
| BR-CART-014 | Coupon must not exceed max uses (`max_uses IS NULL OR used_count < max_uses`) |
| BR-CART-015 | Cart subtotal (before discount) must be ≥ `coupon.min_order_amount` |
| BR-CART-016 | FLAT coupon: `discount_amount = MIN(coupon.value, subtotal)` — cannot exceed cart subtotal |
| BR-CART-017 | PERCENT coupon: `discount_amount = ROUND(subtotal × value/100, 2)` — no maximum cap (Q5:C) |
| BR-CART-018 | `used_count` is incremented by Order Service when an order is placed, NOT by Cart Service on apply |
| BR-CART-019 | If an applied coupon becomes invalid between apply and checkout (expired, deactivated, max_uses reached), Order Service must re-validate — Cart Service returns current coupon state in cart totals |
| BR-CART-020 | Admin can create, update, and deactivate coupons via admin endpoints |

---

## Pricing / Totals Rules

| ID | Rule |
|---|---|
| BR-CART-021 | Shipping charge = ₹0.00 always (free shipping — Q1:A) |
| BR-CART-022 | GST = 5% on sarees, displayed as a **separate line item** in cart totals (Q2:B) |
| BR-CART-023 | GST is calculated on `subtotal - discount_amount` (tax on the net payable amount, not MRP) |
| BR-CART-024 | All monetary values stored and returned as `Decimal(10,2)` with INR currency |
| BR-CART-025 | Total = `(subtotal - discount_amount) + gst_amount + shipping_charge` |
| BR-CART-026 | Product prices are fetched from Product Service in real-time at cart totals calculation; CartItem stores only product_id + quantity (no price snapshot) |
| BR-CART-027 | If Product Service is unreachable at totals calculation, return cached last-known price with `price_stale: true` flag and 206 Partial Content |

---

## Wishlist Rules

| ID | Rule |
|---|---|
| BR-CART-028 | One wishlist per user; created automatically on first add |
| BR-CART-029 | Add to wishlist is idempotent — adding already-wishlisted product returns 200 without error |
| BR-CART-030 | No limit on number of wishlist items |
| BR-CART-031 | Wishlist items display current product price and availability (fetched live from Product Service) |

---

## Input Validation Rules

| ID | Rule |
|---|---|
| BR-CART-032 | product_id: valid UUID format |
| BR-CART-033 | quantity: integer 1–10 |
| BR-CART-034 | coupon code: 1–50 chars, alphanumeric + hyphens only |
| BR-CART-035 | Coupon value: > 0; PERCENT type value must be ≤ 100 |
