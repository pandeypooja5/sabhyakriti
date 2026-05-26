# Business Rules — Unit 2: Product Microservice

---

## Filtering & Search Rules

| ID | Rule |
|---|---|
| BR-PROD-001 | PLP filter combination: **within-dimension OR, cross-dimension AND** — e.g., selecting Silk + Cotton (FABRIC) and Bridal + Party (OCCASION) returns products that are (Silk OR Cotton) AND (Bridal OR Party) |
| BR-PROD-002 | A product with no categories in a given dimension is excluded when any filter of that dimension is active |
| BR-PROD-003 | Applying zero filters returns all active products (no dimension restrictions) |
| BR-PROD-004 | PLP only shows products where `is_active = TRUE` |
| BR-PROD-005 | Search uses PostgreSQL full-text search (`tsvector`) over `name`, `description`, and associated category names |
| BR-PROD-006 | `search_vector` is maintained by a PostgreSQL `AFTER INSERT OR UPDATE` trigger on the products table |
| BR-PROD-007 | Search and category filters can be combined: filtered results are then full-text ranked |
| BR-PROD-008 | Search query is processed with `plainto_tsquery('english', query)` to handle multi-word inputs safely |

---

## Sorting Rules

| ID | Rule |
|---|---|
| BR-PROD-009 | Default sort: `NEWEST` — `ORDER BY created_at DESC` |
| BR-PROD-010 | `PRICE_ASC`: `ORDER BY discounted_price ASC` (computed as `price * (1 - discount_percentage/100)`) |
| BR-PROD-011 | `PRICE_DESC`: `ORDER BY discounted_price DESC` |
| BR-PROD-012 | `RATING_DESC`: `ORDER BY average_rating DESC, review_count DESC` (rating tie-break by review count) |
| BR-PROD-013 | `POPULARITY`: `ORDER BY review_count DESC, average_rating DESC` |
| BR-PROD-014 | When search query is active, results are also ranked by `ts_rank` — ties broken by the selected sort |

---

## Pagination Rules

| ID | Rule |
|---|---|
| BR-PROD-015 | Default page size: 24 products per page |
| BR-PROD-016 | Maximum page size: 48 products per page |
| BR-PROD-017 | Minimum page size: 1; invalid page sizes return HTTP 422 |
| BR-PROD-018 | Out-of-range page numbers return empty results (not 404) |
| BR-PROD-019 | Response includes `total_count`, `page`, `page_size`, `total_pages` for frontend pagination controls |

---

## Pricing & Discount Rules

| ID | Rule |
|---|---|
| BR-PROD-020 | `price` (MRP) must be > 0 INR |
| BR-PROD-021 | `discount_percentage` is 0–100; 0 means no discount |
| BR-PROD-022 | `discounted_price = ROUND(price × (1 − discount_percentage / 100), 2)` — computed, not stored |
| BR-PROD-023 | When `discount_percentage = 0`, `discounted_price = price` (no separate display of MRP) |
| BR-PROD-024 | Frontend receives both `price` (MRP) and `discounted_price`; calculates display `% off` as `ROUND(discount_percentage)` |

---

## Stock & Availability Rules

| ID | Rule |
|---|---|
| BR-PROD-025 | `stock_qty = 0` → `StockStatus.OUT_OF_STOCK` |
| BR-PROD-026 | `0 < stock_qty ≤ 5` → `StockStatus.LOW_STOCK` |
| BR-PROD-027 | `stock_qty > 5` → `StockStatus.IN_STOCK` |
| BR-PROD-028 | Product Service exposes an **internal** endpoint `PATCH /internal/v1/products/{id}/stock` for Order Service to decrement/increment stock atomically (using `UPDATE … SET stock_qty = stock_qty - delta WHERE stock_qty >= delta`) |
| BR-PROD-029 | Stock never goes below 0; if `delta > stock_qty`, the internal endpoint returns HTTP 409 Conflict |

---

## Product Slug Rules

| ID | Rule |
|---|---|
| BR-PROD-030 | Slug auto-generated at creation: lowercase, spaces→hyphens, strip non-alphanumeric except hyphens |
| BR-PROD-031 | Slug max length: 220 chars (truncated from name if needed, before suffix) |
| BR-PROD-032 | On collision (same slug exists): append `-{first-8-chars-of-uuid}` suffix and retry once |
| BR-PROD-033 | Slug is immutable after creation — changing the product name does NOT change the slug (prevents broken URLs) |
| BR-PROD-034 | Admin may not manually set slug via API — always auto-generated |

---

## Product Image Rules

| ID | Rule |
|---|---|
| BR-PROD-035 | Maximum 10 images per product; attempt to add an 11th returns HTTP 400 |
| BR-PROD-036 | Exactly one image must be designated `is_primary = TRUE` per product that has images |
| BR-PROD-037 | If primary image is deleted, the image with the lowest `sort_order` is automatically promoted to primary |
| BR-PROD-038 | S3 presigned upload URL TTL = 15 minutes |
| BR-PROD-039 | Image is not visible until `confirm_image_upload` is called — prevents orphaned S3 objects appearing in product |
| BR-PROD-040 | S3 key format: `products/{product_id}/{uuid}.{ext}` |
| BR-PROD-041 | CloudFront URL format: `https://cdn.sabhyakriti.com/{s3_key}` |
| BR-PROD-042 | Allowed image extensions: `.jpg`, `.jpeg`, `.png`, `.webp` |

---

## Review Rules

| ID | Rule |
|---|---|
| BR-PROD-043 | Only one review per user per product (enforced by DB UNIQUE constraint) |
| BR-PROD-044 | Verified purchase check: Product Service calls Order Service `GET /internal/v1/orders/verified-purchase?user_id=&product_id=` before creating review; if Order Service returns `false`, HTTP 403 "You must purchase and receive this product before reviewing it" |
| BR-PROD-045 | Rating must be 1–5 (integer) |
| BR-PROD-046 | Review title: 1–150 chars; body: optional, max 2000 chars |
| BR-PROD-047 | On review create: update `Product.average_rating = ROUND(AVG(rating), 2)` and `Product.review_count` atomically |
| BR-PROD-048 | On review delete: recalculate `average_rating` and `review_count` |
| BR-PROD-049 | `is_verified_purchase` is set at creation time based on Order Service response; cannot be changed after creation |
| BR-PROD-050 | Reviews are returned paginated (default 10 per page), ordered by `created_at DESC` |
| BR-PROD-051 | Admin can delete any review; user can delete only their own review |

---

## Admin & Catalog Rules

| ID | Rule |
|---|---|
| BR-PROD-052 | Product deletion is **soft-delete** (`is_active = FALSE`); hard-delete not supported |
| BR-PROD-053 | Deactivated products are excluded from all customer-facing endpoints |
| BR-PROD-054 | A product must have at least one category assigned before it can be activated |
| BR-PROD-055 | Category deletion blocked if any active products are assigned to it |
| BR-PROD-056 | Category names are case-insensitive; normalized to title case on save |
| BR-PROD-057 | Bulk CSV import: rows with validation errors are collected and returned as `failed_rows[]`; valid rows are imported regardless |
| BR-PROD-058 | Bulk CSV max row limit: 500 rows per request |
| BR-PROD-059 | On bulk import, if a SKU already exists, the row **updates** the existing product (upsert by SKU) |
| BR-PROD-060 | Category names in CSV are matched case-insensitively; unknown category names create a validation error for that row |

---

## Input Validation Rules

| ID | Rule |
|---|---|
| BR-PROD-061 | Product name: 1–200 chars, strip leading/trailing whitespace |
| BR-PROD-062 | Price: positive Decimal, max 2 decimal places, max value 999999.99 |
| BR-PROD-063 | Discount percentage: 0.00–100.00, max 2 decimal places |
| BR-PROD-064 | Stock quantity: non-negative integer, max 99999 |
| BR-PROD-065 | Review rating: integer 1–5 |
