# Domain Entities — Unit 4: Order Microservice

---

## Entity: Order

| Field | Type | Constraints | Description |
|---|---|---|---|
| `order_id` | UUID | PK | |
| `order_number` | VARCHAR(30) | UNIQUE, NOT NULL | Human-readable: `SKB-YYYYMM-{seq:06d}` |
| `user_id` | UUID | NOT NULL | FK-like ref to Auth Service |
| `status` | VARCHAR(30) | NOT NULL | See OrderStatus enum |
| `payment_method` | VARCHAR(20) | NOT NULL | `RAZORPAY`, `UPI`, `COD` |
| `subtotal` | NUMERIC(10,2) | NOT NULL | Sum of item totals before discount |
| `discount_amount` | NUMERIC(10,2) | NOT NULL, DEFAULT 0 | Coupon discount applied |
| `gst_amount` | NUMERIC(10,2) | NOT NULL | 5% GST on (subtotal − discount) |
| `shipping_charge` | NUMERIC(10,2) | NOT NULL, DEFAULT 0 | Always ₹0 for now |
| `total_amount` | NUMERIC(10,2) | NOT NULL | Final amount paid/to be paid |
| `coupon_code_used` | VARCHAR(50) | nullable | Coupon code at time of order |
| `shipping_address` | JSONB | NOT NULL | Full address snapshot (denormalised) |
| `tracking_number` | VARCHAR(100) | nullable | Set by admin on SHIPPED status |
| `courier_name` | VARCHAR(100) | nullable | E.g., "Delhivery", "BlueDart" |
| `notes` | TEXT | nullable | Admin internal notes |
| `placed_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Order creation time |
| `confirmed_at` | TIMESTAMPTZ | nullable | |
| `shipped_at` | TIMESTAMPTZ | nullable | |
| `delivered_at` | TIMESTAMPTZ | nullable | Marks start of 7-day return window |
| `cancelled_at` | TIMESTAMPTZ | nullable | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Indexes**: `user_id`, `status`, `placed_at DESC`, `order_number` (unique)

---

## Entity: OrderItem

| Field | Type | Constraints | Description |
|---|---|---|---|
| `order_item_id` | UUID | PK | |
| `order_id` | UUID | FK → Order, NOT NULL | |
| `product_id` | UUID | NOT NULL | Reference (no DB FK across services) |
| `product_name` | VARCHAR(200) | NOT NULL | Snapshot at order time |
| `product_image_url` | VARCHAR(600) | nullable | Primary image CloudFront URL snapshot |
| `quantity` | SMALLINT | NOT NULL, ≥ 1 | |
| `unit_price` | NUMERIC(10,2) | NOT NULL | MRP snapshot |
| `discounted_price` | NUMERIC(10,2) | NOT NULL | Selling price snapshot |
| `item_total` | NUMERIC(10,2) | NOT NULL | `quantity × discounted_price` |

**Indexes**: `order_id`

---

## Entity: Address

| Field | Type | Constraints | Description |
|---|---|---|---|
| `address_id` | UUID | PK | |
| `user_id` | UUID | NOT NULL | |
| `full_name` | VARCHAR(100) | NOT NULL | Recipient name |
| `phone` | VARCHAR(15) | NOT NULL | Delivery contact |
| `address_line1` | VARCHAR(200) | NOT NULL | Street, building |
| `address_line2` | VARCHAR(200) | nullable | Area, landmark |
| `city` | VARCHAR(100) | NOT NULL | |
| `state` | VARCHAR(100) | NOT NULL | |
| `pincode` | VARCHAR(10) | NOT NULL | Indian PIN code (6 digits) |
| `is_default` | BOOLEAN | NOT NULL, DEFAULT FALSE | |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Indexes**: `user_id`, partial unique on `(user_id)` WHERE `is_default = TRUE`

---

## Entity: ReturnRequest

| Field | Type | Constraints | Description |
|---|---|---|---|
| `return_id` | UUID | PK | |
| `order_id` | UUID | FK → Order, NOT NULL | |
| `user_id` | UUID | NOT NULL | |
| `status` | VARCHAR(30) | NOT NULL | See ReturnStatus enum |
| `reason` | VARCHAR(500) | NOT NULL | Customer's reason |
| `admin_notes` | TEXT | nullable | Admin decision notes |
| `refund_amount` | NUMERIC(10,2) | nullable | Calculated on approval |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Constraints**: UNIQUE `order_id` — one return request per order (can include multiple items)

---

## Entity: ReturnItem

| Field | Type | Constraints | Description |
|---|---|---|---|
| `return_item_id` | UUID | PK | |
| `return_id` | UUID | FK → ReturnRequest, NOT NULL | |
| `order_item_id` | UUID | FK → OrderItem, NOT NULL | Identifies which item |
| `quantity` | SMALLINT | NOT NULL, ≥ 1 | Units to return (≤ ordered quantity) |
| `reason` | VARCHAR(200) | nullable | Per-item reason |

---

## Value Objects

| Value Object | Values |
|---|---|
| `OrderStatus` | `PENDING` → `CONFIRMED` → `SHIPPED` → `DELIVERED`; branches: `CANCELLED`, `RETURN_REQUESTED`, `RETURN_APPROVED`, `RETURN_REJECTED`, `RETURNED`, `REFUNDED` |
| `ReturnStatus` | `PENDING_REVIEW` → `APPROVED` or `REJECTED`; then `ITEMS_RECEIVED` → `REFUND_INITIATED` → `REFUNDED` |
| `PaymentMethod` | `RAZORPAY`, `UPI`, `COD` |

---

## AddressSnapshot (JSONB structure stored in Order.shipping_address)

```json
{
  "address_id": "uuid",
  "full_name": "Priya Sharma",
  "phone": "9876543210",
  "address_line1": "42, MG Road",
  "address_line2": "Near Central Mall",
  "city": "Bengaluru",
  "state": "Karnataka",
  "pincode": "560001"
}
```
