# Integration Test Instructions — Sabhyakriti Platform

Integration tests validate that all 9 services work together correctly.

---

## Setup: Start All Services

```bash
# From workspace root — starts all 7 backend services + PostgreSQL + Redis
docker-compose -f docker-compose.all.yml up -d

# Wait for all services healthy (check with):
docker-compose -f docker-compose.all.yml ps

# Run all migrations
export DB_PASSWORD=postgres
bash sabhyakriti-infra/scripts/run_migrations.sh localhost
```

Set shared environment:
```bash
export BASE_URL=http://localhost
export INTERNAL_SECRET=dev-internal-secret
```

---

## Scenario 1: User Registration → Email Verification → Login

```bash
# Register
curl -s -X POST $BASE_URL:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass1!","full_name":"Test User"}'
# Expected: 201 {"message": "Registration successful. Please verify your email."}

# Verify email (token from mock email or Auth Service DB)
# In dev: query auth DB: SELECT token_hash FROM auth.email_verification_tokens LIMIT 1;
# Then: GET $BASE_URL:8001/api/v1/auth/verify-email?token={raw_token}
# Expected: 200 {"tokens": {...}, "user": {...}}

# Login
curl -s -X POST $BASE_URL:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass1!"}'
# Expected: 200 with access_token and refresh_token
export ACCESS_TOKEN=$(... | jq -r '.tokens.access_token')
```

---

## Scenario 2: Browse Products (PLP → PDP)

```bash
# List products (no auth required)
curl -s "$BASE_URL:8002/api/v1/products?page=1&page_size=12&sort=NEWEST"
# Expected: 200 with items array and total_count

# Get product detail by slug
curl -s "$BASE_URL:8002/api/v1/products/slug/{product-slug}"
# Expected: 200 with full product detail including images, categories, reviews

# Get categories
curl -s "$BASE_URL:8002/api/v1/categories?type=FABRIC"
# Expected: 200 list of Fabric categories
```

---

## Scenario 3: Cart → Coupon → Order → Payment (Full Checkout)

```bash
AUTH="Authorization: Bearer $ACCESS_TOKEN"

# Add to cart
curl -s -X POST $BASE_URL:8003/api/v1/cart/items \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"product_id":"{product-uuid}","quantity":1}'
# Expected: 200 CartDTO with totals

# Apply coupon (create one via admin first)
curl -s -X POST $BASE_URL:8003/api/v1/cart/coupon \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"coupon_code":"SAVE10"}'
# Expected: 200 CartDTO with discount_amount > 0

# Create address
curl -s -X POST $BASE_URL:8004/api/v1/addresses \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"full_name":"Test User","phone":"9876543210","address_line1":"42 MG Road","city":"Bengaluru","state":"Karnataka","pincode":"560001"}'

# Create order (COD)
curl -s -X POST $BASE_URL:8004/api/v1/orders \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"address_id":"{address-uuid}","payment_method":"COD"}'
# Expected: 201 OrderDTO with status=CONFIRMED, order_number=SKB-*

# Get order
ORDER_ID=$(... | jq -r '.order_id')
curl -s "$BASE_URL:8004/api/v1/orders/$ORDER_ID" -H "$AUTH"
# Expected: 200 OrderDTO
```

---

## Scenario 4: Razorpay Payment Flow

```bash
# Create Razorpay order (requires Razorpay test keys)
curl -s -X POST $BASE_URL:8005/api/v1/payments/create-order \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"order_id":"{order-uuid}","amount":1500.00}'
# Expected: 200 RazorpayOrderDTO with razorpay_order_id

# Simulate webhook (payment.captured)
curl -s -X POST $BASE_URL:8005/api/v1/payments/webhook \
  -H "Content-Type: application/json" \
  -H "X-Razorpay-Signature: {computed-hmac}" \
  -d '{"event":"payment.captured","payload":{"payment":{"entity":{"id":"pay_xxx","order_id":"order_xxx","amount":150000}}}}'
# Expected: 200 (Order Service notified, order status → CONFIRMED)
```

---

## Scenario 5: Admin Order Lifecycle

```bash
ADMIN_TOKEN=$(curl -s -X POST $BASE_URL:8001/api/v1/auth/login \
  -d '{"email":"admin@sabhyakriti.com","password":"AdminPass1!"}' | jq -r '.tokens.access_token')
ADMIN_AUTH="Authorization: Bearer $ADMIN_TOKEN"

# Update order to SHIPPED
curl -s -X PATCH $BASE_URL:8007/api/v1/admin/orders/$ORDER_ID/status \
  -H "$ADMIN_AUTH" -H "Content-Type: application/json" \
  -d '{"status":"SHIPPED","tracking_number":"DL123456789","courier_name":"Delhivery"}'
# Expected: 200 OrderDTO with status=SHIPPED, notification triggered

# Advance to DELIVERED
curl -s -X PATCH $BASE_URL:8007/api/v1/admin/orders/$ORDER_ID/status \
  -H "$ADMIN_AUTH" -H "Content-Type: application/json" \
  -d '{"status":"DELIVERED"}'
# Expected: 200 OrderDTO with status=DELIVERED, delivered_at set
```

---

## Scenario 6: Product Review (Verified Purchase)

```bash
# Submit review (user must have DELIVERED order with this product)
curl -s -X POST $BASE_URL:8002/api/v1/reviews \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"product_id":"{product-uuid}","rating":5,"title":"Stunning!","body":"Quality is excellent."}'
# Expected: 201 ReviewDTO with is_verified_purchase=true
# Product average_rating updated automatically
```

---

## Scenario 7: Return Request Flow

```bash
# Submit return (within 7 days of delivery)
curl -s -X POST $BASE_URL:8004/api/v1/orders/$ORDER_ID/returns \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"reason":"Color different from photos","items":[{"order_item_id":"{item-uuid}","quantity":1}]}'
# Expected: 201 ReturnRequestDTO with status=PENDING_REVIEW

# Admin approves return
curl -s -X POST $BASE_URL:8007/api/v1/admin/returns/{return-id}/process \
  -H "$ADMIN_AUTH" -H "Content-Type: application/json" \
  -d '{"action":"APPROVE","admin_notes":"Valid return request"}'
# Expected: 200 ReturnRequestDTO with status=APPROVED

# Admin initiates refund
curl -s -X POST $BASE_URL:8007/api/v1/admin/returns/{return-id}/initiate-refund \
  -H "$ADMIN_AUTH"
# Expected: 200 with status=REFUNDED; Payment Service refund API called
```

---

## Cleanup

```bash
docker-compose -f docker-compose.all.yml down -v
# -v removes volumes (clears DB data)
```
