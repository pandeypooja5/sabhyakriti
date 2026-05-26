# Domain Entities — Unit 2: Product Microservice

---

## Entity: Product

| Field | Type | Constraints | Description |
|---|---|---|---|
| `product_id` | UUID | PK | Auto-generated |
| `name` | VARCHAR(200) | NOT NULL | Display name |
| `slug` | VARCHAR(220) | UNIQUE, NOT NULL | Auto-generated URL-safe slug; UUID suffix on collision |
| `sku` | VARCHAR(100) | UNIQUE, nullable | Stock Keeping Unit; admin-assigned |
| `description` | TEXT | nullable | Rich product description |
| `price` | NUMERIC(10,2) | NOT NULL, > 0 | MRP / original price in INR |
| `discount_percentage` | NUMERIC(5,2) | NOT NULL, DEFAULT 0, 0–100 | Admin-set discount; `discounted_price = price × (1 - pct/100)` |
| `stock_qty` | INTEGER | NOT NULL, DEFAULT 0, ≥ 0 | Current stock; decremented by Order Service |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | FALSE = soft-deleted; hidden from PLP |
| `average_rating` | NUMERIC(3,2) | NOT NULL, DEFAULT 0.00, 0–5 | Denormalised; recalculated on review insert/delete |
| `review_count` | INTEGER | NOT NULL, DEFAULT 0 | Denormalised count of approved reviews |
| `search_vector` | TSVECTOR | nullable | PostgreSQL FTS vector over name + description + category names; updated by trigger |
| `blouse_included` | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether blouse piece is included |
| `fabric_description` | VARCHAR(200) | nullable | E.g., "Pure Banarasi Silk, 6.3m saree + 0.8m blouse" |
| `care_instructions` | TEXT | nullable | Washing/storage instructions |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Auto-updated |

**Indexes**: `slug` (unique), `is_active` (partial index where `is_active = TRUE`), `search_vector` (GIN index for FTS), `stock_qty` (for low-stock queries), `average_rating` (for popularity sort), `created_at` (for newest sort)

**Computed (not stored)**:
- `discounted_price` = `price × (1 − discount_percentage / 100)` — computed in application layer
- `discount_amount` = `price − discounted_price`
- `discount_percent_display` = `discount_percentage` (rounded to nearest integer for display)
- `stock_status` = `OUT_OF_STOCK` if stock_qty = 0 | `LOW_STOCK` if stock_qty ≤ 5 | `IN_STOCK` otherwise

---

## Entity: Category

| Field | Type | Constraints | Description |
|---|---|---|---|
| `category_id` | UUID | PK | Auto-generated |
| `name` | VARCHAR(100) | NOT NULL | E.g., "Silk", "Bridal", "Banarasi" |
| `type` | VARCHAR(20) | NOT NULL | Enum: `FABRIC`, `OCCASION`, `REGION` |
| `slug` | VARCHAR(120) | UNIQUE, NOT NULL | URL-safe, auto-generated |
| `display_order` | SMALLINT | NOT NULL, DEFAULT 0 | Sort order within type for PLP filter sidebar |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Indexes**: `(type, is_active)` composite, `slug` (unique)

**Seed data** (from requirements):
- FABRIC: Silk, Cotton, Georgette, Chiffon, Chanderi, Linen, Net, Banarasi Brocade
- OCCASION: Bridal, Party, Casual, Festive, Office, Wedding, Daily Wear
- REGION: Banarasi, Kanjivaram, Bandhani, Pochampally, Paithani, Sambalpuri, Chanderi, Jamdani

---

## Entity: ProductCategory (Join Table)

| Field | Type | Constraints | Description |
|---|---|---|---|
| `product_id` | UUID | FK → Product, NOT NULL | |
| `category_id` | UUID | FK → Category, NOT NULL | |
| PK | composite | `(product_id, category_id)` | |

**Indexes**: `product_id`, `category_id`

---

## Entity: ProductImage

| Field | Type | Constraints | Description |
|---|---|---|---|
| `image_id` | UUID | PK | |
| `product_id` | UUID | FK → Product, NOT NULL | |
| `s3_key` | VARCHAR(500) | NOT NULL, UNIQUE | S3 object key (e.g., `products/{product_id}/{uuid}.jpg`) |
| `cloudfront_url` | VARCHAR(600) | NOT NULL | Full CDN URL for serving |
| `is_primary` | BOOLEAN | NOT NULL, DEFAULT FALSE | At most one primary image per product |
| `sort_order` | SMALLINT | NOT NULL, DEFAULT 0 | Display order in image gallery |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Constraints**: Partial unique index on `(product_id, is_primary)` WHERE `is_primary = TRUE` — enforces at most one primary image per product.

**Business rule**: Max 10 images per product.

**Indexes**: `product_id`, `(product_id, sort_order)` for ordered gallery fetch

---

## Entity: Review

| Field | Type | Constraints | Description |
|---|---|---|---|
| `review_id` | UUID | PK | |
| `product_id` | UUID | FK → Product, NOT NULL | |
| `user_id` | UUID | NOT NULL | FK-like reference to Auth Service user (no DB FK across services) |
| `rating` | SMALLINT | NOT NULL, 1–5 | Star rating |
| `title` | VARCHAR(150) | NOT NULL | Review headline |
| `body` | TEXT | nullable | Review body text |
| `is_verified_purchase` | BOOLEAN | NOT NULL, DEFAULT FALSE | Set TRUE if Order Service confirms DELIVERED order |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | |

**Constraints**: UNIQUE `(product_id, user_id)` — one review per user per product.

**Indexes**: `product_id`, `(product_id, created_at DESC)` for paginated review list, `user_id`

---

## Value Objects

| Value Object | Type | Values |
|---|---|---|
| `CategoryType` | Enum | `FABRIC`, `OCCASION`, `REGION` |
| `StockStatus` | Enum | `IN_STOCK`, `LOW_STOCK`, `OUT_OF_STOCK` |
| `SortOrder` | Enum | `NEWEST`, `PRICE_ASC`, `PRICE_DESC`, `RATING_DESC`, `POPULARITY` |
| `Money` | VO | `Decimal` amount + currency (`INR`); `discounted(pct)` method |

---

## CSV Bulk Import Row

Represents one row in admin bulk upload CSV:

| Column | Required | Validation |
|---|---|---|
| `name` | Yes | 1–200 chars |
| `description` | No | max 5000 chars |
| `price` | Yes | positive decimal |
| `discount_percentage` | No | 0–100, default 0 |
| `stock_qty` | Yes | non-negative integer |
| `sku` | No | max 100 chars, unique |
| `fabric_categories` | No | comma-separated category names (FABRIC type) |
| `occasion_categories` | No | comma-separated (OCCASION type) |
| `region_categories` | No | comma-separated (REGION type) |
| `blouse_included` | No | `true`/`false`, default `false` |
| `fabric_description` | No | max 200 chars |
| `care_instructions` | No | max 1000 chars |
