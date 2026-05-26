# Contract Test Instructions — Sabhyakriti Microservices

Contract tests validate that service-to-service API contracts are respected.
These prevent breaking changes from one service silently breaking its callers.

---

## Critical API Contracts to Validate

### Contract 1: Auth Service — JWT Public Key (JWKS)

All other services fetch the RS256 public key at startup. Validate the JWKS endpoint format:

```bash
curl -s http://localhost:8001/auth/.well-known/jwks.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
assert 'keys' in data, 'Missing keys array'
assert len(data['keys']) >= 1, 'No keys present'
key = data['keys'][0]
assert key.get('kty') == 'RSA', 'Key type must be RSA'
assert key.get('alg') == 'RS256', 'Algorithm must be RS256'
assert 'n' in key and 'e' in key, 'Missing RSA components n/e'
print('JWKS contract: PASS')
"
```

---

### Contract 2: Product Service — Internal Stock Endpoint

Order Service calls this to reserve/release stock. Validate the contract:

```bash
INTERNAL_SECRET="dev-internal-secret"
PRODUCT_ID="<uuid>"

# Reserve stock
curl -s -X PATCH http://localhost:8002/internal/v1/products/$PRODUCT_ID/stock \
  -H "X-Internal-Secret: $INTERNAL_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"delta": 1}' | python3 -c "
import json, sys
data = json.load(sys.stdin)
assert 'product_id' in data, 'Missing product_id'
assert 'new_stock_qty' in data, 'Missing new_stock_qty'
assert 'stock_status' in data, 'Missing stock_status'
assert data['stock_status'] in ('IN_STOCK','LOW_STOCK','OUT_OF_STOCK'), 'Invalid stock_status'
print('Product stock contract: PASS')
"

# Insufficient stock → 409
curl -s -o /dev/null -w "%{http_code}\n" \
  -X PATCH http://localhost:8002/internal/v1/products/$PRODUCT_ID/stock \
  -H "X-Internal-Secret: $INTERNAL_SECRET" \
  -d '{"delta": 99999}'
# Expected: 409
```

---

### Contract 3: Cart Service — Internal Read/Clear Cart

Order Service calls this during checkout:

```bash
USER_ID="<uuid>"

# Read cart
curl -s http://localhost:8003/internal/v1/cart/$USER_ID \
  -H "X-Internal-Secret: $INTERNAL_SECRET" | python3 -c "
import json, sys
data = json.load(sys.stdin)
assert 'cart_id' in data, 'Missing cart_id'
assert 'items' in data, 'Missing items'
assert 'totals' in data, 'Missing totals'
totals = data['totals']
assert 'subtotal' in totals and 'gst_amount' in totals and 'total' in totals
print('Cart read contract: PASS')
"

# Clear cart
curl -s -X DELETE http://localhost:8003/internal/v1/cart/$USER_ID \
  -H "X-Internal-Secret: $INTERNAL_SECRET" -w "%{http_code}"
# Expected: 204
```

---

### Contract 4: Order Service — Confirm Order (Payment → Order)

```bash
ORDER_ID="<uuid>"

curl -s -X POST http://localhost:8004/internal/v1/orders/$ORDER_ID/confirm \
  -H "X-Internal-Secret: $INTERNAL_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"payment_id":"pay_test123"}' | python3 -c "
import json, sys
data = json.load(sys.stdin)
assert data.get('status') == 'CONFIRMED', f'Expected CONFIRMED, got {data.get(\"status\")}'
assert 'confirmed_at' in data, 'Missing confirmed_at timestamp'
print('Order confirm contract: PASS')
"
```

---

### Contract 5: Notification Service — Internal Endpoints

```bash
# Test order confirmation email endpoint
curl -s -X POST http://localhost:8006/internal/v1/notifications/email/order-confirmation \
  -H "X-Internal-Secret: $INTERNAL_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "to_email": "test@example.com", "full_name": "Test",
    "order_number": "SKB-202605-000001",
    "items": [{"name":"Silk Saree","qty":1,"price":"1500.00"}],
    "subtotal": "1500.00", "discount_amount": "0.00",
    "gst_amount": "75.00", "total": "1575.00",
    "shipping_address": {"city":"Bengaluru"},
    "payment_method": "COD"
  }' -w "%{http_code}"
# Expected: 202 (fire-and-forget)
```

---

### Contract 6: Product Service — Verified Purchase Check

```bash
curl -s "http://localhost:8002/internal/v1/products/verified-purchase?user_id=$USER_ID&product_id=$PRODUCT_ID" \
  -H "X-Internal-Secret: $INTERNAL_SECRET" | python3 -c "
import json, sys
data = json.load(sys.stdin)
assert 'verified' in data, 'Missing verified field'
assert isinstance(data['verified'], bool), 'verified must be bool'
print('Verified purchase contract: PASS')
"
```

---

## Run All Contract Tests

```bash
bash scripts/run_contract_tests.sh
# Runs all 6 contracts above sequentially; exits non-zero on first failure
```
