# Business Logic Model — Unit 2: Product Microservice

---

## Flow 1: PLP — List Products (Customer)

```
Input: fabric_ids[], occasion_ids[], region_ids[], search, sort, page, page_size

1. Validate page_size (1–48, default 24), page (≥ 1, default 1) → 422 if invalid
2. Base query: SELECT products WHERE is_active = TRUE
3. Apply category filters (BR-PROD-001):
   IF fabric_ids non-empty:
     product_id IN (SELECT product_id FROM product_categories WHERE category_id IN fabric_ids)
   IF occasion_ids non-empty:
     AND product_id IN (SELECT product_id FROM product_categories WHERE category_id IN occasion_ids)
   IF region_ids non-empty:
     AND product_id IN (SELECT product_id FROM product_categories WHERE category_id IN region_ids)
4. Apply search (BR-PROD-005, BR-PROD-008):
   IF search non-empty:
     AND search_vector @@ plainto_tsquery('english', search)
5. Apply sort (BR-PROD-009–014):
   NEWEST         → ORDER BY created_at DESC
   PRICE_ASC      → ORDER BY (price * (1 - discount_percentage/100)) ASC
   PRICE_DESC     → ORDER BY (price * (1 - discount_percentage/100)) DESC
   RATING_DESC    → ORDER BY average_rating DESC, review_count DESC
   POPULARITY     → ORDER BY review_count DESC, average_rating DESC
   (with search)  → also include ts_rank as secondary sort
6. COUNT total results (for pagination metadata)
7. Apply LIMIT + OFFSET
8. For each product, fetch primary image from product_images WHERE is_primary = TRUE
9. Compute: discounted_price, stock_status, discount_percent_display
10. Return PagedProductListDTO {
      items: [ProductSummaryDTO],
      total_count, page, page_size, total_pages
    }
```

---

## Flow 2: PDP — Get Product Detail (Customer)

```
Input: product_id OR slug

1. Lookup by product_id or slug → 404 if not found OR is_active = FALSE
2. Fetch product with all images (ORDER BY sort_order ASC)
3. Fetch all category IDs + names for this product (grouped by type)
4. Compute: discounted_price, stock_status, discount_percent_display
5. Fetch first page of reviews (10 reviews, ORDER BY created_at DESC)
6. Fetch related products:
   a. Get category IDs of this product
   b. SELECT products sharing ≥1 category, WHERE is_active = TRUE, EXCLUDE current product
   c. ORDER BY average_rating DESC LIMIT 8
7. Return ProductDetailDTO {
     product fields,
     images (sorted),
     categories { fabric:[], occasion:[], region:[] },
     discounted_price, stock_status,
     reviews: PagedReviewsDTO (first page),
     related_products: [ProductSummaryDTO]
   }
```

---

## Flow 3: Get Presigned Upload URL (Admin)

```
Input: product_id, file_extension (jpg/jpeg/png/webp)

1. Validate admin role
2. Validate file_extension against allowed list (BR-PROD-042) → 400 if invalid
3. Count existing images for product → if ≥ 10: HTTP 400 "Maximum 10 images per product"
4. Generate s3_key = f"products/{product_id}/{uuid4()}.{ext}"
5. Call AWSS3Adapter.generate_presigned_put_url(s3_key, TTL=900s, content_type="image/{ext}")
6. Return PresignedUrlDTO { presigned_url, s3_key, expires_in: 900 }
```

---

## Flow 4: Confirm Image Upload (Admin)

```
Input: product_id, s3_key, is_primary (bool), sort_order (int)

1. Validate admin role
2. Verify s3_key belongs to this product (prefix check: starts with "products/{product_id}/")
3. Build cloudfront_url = f"https://cdn.sabhyakriti.com/{s3_key}"
4. IF is_primary = TRUE:
   UPDATE product_images SET is_primary = FALSE WHERE product_id = product_id
5. Create ProductImage { product_id, s3_key, cloudfront_url, is_primary, sort_order }
6. Return ProductImageDTO
```

---

## Flow 5: Delete Product Image (Admin)

```
Input: product_id, image_id

1. Validate admin role
2. Load image → 404 if not found for this product
3. Delete image record from DB
4. IF deleted image was primary AND other images remain:
   UPDATE product_images SET is_primary = TRUE
   WHERE id = (SELECT id FROM product_images WHERE product_id = X ORDER BY sort_order ASC LIMIT 1)
5. (S3 object remains; physical cleanup is separate admin operation or S3 lifecycle policy)
6. Return 204 No Content
```

---

## Flow 6: Submit Review (Customer)

```
Input: product_id, rating, title, body (auth required)

1. Validate user is authenticated
2. Check UNIQUE (product_id, user_id) → 409 "You have already reviewed this product" if exists
3. Call Order Service (internal): GET /internal/v1/orders/verified-purchase?user_id=&product_id=
   → 503 if Order Service unavailable (do not fail review; proceed with is_verified_purchase=False)
   → True/False response sets is_verified_purchase
4. IF is_verified_purchase = False (and Order Service was reachable): HTTP 403 (BR-PROD-044)
5. Create Review { product_id, user_id, rating, title, body, is_verified_purchase }
6. Update Product atomically:
   UPDATE products
   SET average_rating = ROUND((average_rating * review_count + new_rating) / (review_count + 1), 2),
       review_count = review_count + 1
   WHERE product_id = ?
7. Return ReviewDTO
```

---

## Flow 7: Delete Review (Customer or Admin)

```
Input: review_id

1. Load review → 404 if not found
2. Authorisation: IF current user is CUSTOMER AND review.user_id ≠ current_user_id → 403
3. Delete review record
4. Recalculate product stats:
   SELECT ROUND(AVG(rating), 2), COUNT(*) FROM reviews WHERE product_id = ?
   UPDATE products SET average_rating = ?, review_count = ? WHERE product_id = ?
5. Return 204
```

---

## Flow 8: Create Product (Admin)

```
Input: name, description, price, discount_percentage, stock_qty, category_ids[], sku?,
       blouse_included, fabric_description, care_instructions

1. Validate admin role
2. Validate all input fields (BR-PROD-061–065)
3. Validate price > 0, discount_percentage in [0, 100]
4. Validate SKU uniqueness if provided → 409 if duplicate
5. Generate slug (BR-PROD-030–032):
   a. slugify(name) = lowercase, spaces→hyphens, strip non-alphanum except hyphens
   b. Truncate to 212 chars if needed
   c. Check uniqueness: if collision append "-{uuid[:8]}"
6. Validate category_ids exist and are active
7. INSERT Product (is_active = FALSE until at least one image is added — or keep TRUE for catalog-first approach)
8. INSERT ProductCategory rows for each category_id
9. Return ProductDetailDTO
```

---

## Flow 9: Update Product (Admin)

```
Input: product_id, partial update fields

1. Validate admin role
2. Load product → 404 if not found
3. Apply only provided fields (partial update / PATCH semantics)
4. If name changed: do NOT update slug (BR-PROD-033)
5. If category_ids provided: replace all ProductCategory rows for this product
6. UPDATE Product
7. Return ProductDetailDTO
```

---

## Flow 10: Bulk CSV Import (Admin)

```
Input: CSV file (multipart upload, max 500 rows)

1. Validate admin role
2. Parse CSV → collect all rows
3. Validate row count ≤ 500 (BR-PROD-058) → 400 if exceeded
4. For each row:
   a. Validate required fields (name, price, stock_qty) — collect errors
   b. Match fabric/occasion/region category names (case-insensitive) → error if unknown
   c. IF sku provided AND product with that SKU exists → update mode
   d. IF no matching SKU → create mode (generate slug)
5. Import valid rows in a single DB transaction:
   - Batch INSERT for new products
   - Batch UPDATE for existing products (by SKU)
   - Batch INSERT ProductCategory rows
6. Return BulkImportResultDTO { imported_count, updated_count, failed_rows: [{row, errors}] }
```

---

## Flow 11: Stock Reserve / Release (Internal — called by Order Service)

```
Input: product_id, delta (positive = decrement, negative = increment)

1. Validate internal auth token (shared secret header)
2. IF delta > 0 (reserve):
   UPDATE products SET stock_qty = stock_qty - delta
   WHERE product_id = ? AND stock_qty >= delta
   → If 0 rows updated: HTTP 409 "Insufficient stock"
3. IF delta < 0 (release):
   UPDATE products SET stock_qty = stock_qty + ABS(delta)
   WHERE product_id = ?
4. Return { product_id, new_stock_qty, stock_status }
```

---

## Error Response Standards

| Scenario | HTTP | Message |
|---|---|---|
| Product not found | 404 | "Product not found." |
| Duplicate review | 409 | "You have already reviewed this product." |
| Review not verified | 403 | "You must purchase and receive this product before reviewing it." |
| Max images reached | 400 | "Maximum 10 images per product." |
| Insufficient stock (internal) | 409 | "Insufficient stock for product {id}." |
| Unknown category in CSV | 422 | Row error: "Unknown category name: '{name}'" |
| Invalid sort value | 422 | "Invalid sort value. Must be one of: NEWEST, PRICE_ASC, PRICE_DESC, RATING_DESC, POPULARITY" |
