# Performance Test Instructions — Sabhyakriti Platform

---

## Performance Requirements (from NFR)

| Endpoint | p95 Target |
|---|---|
| PLP list (cache hit) | < 300ms |
| PLP list (cache miss) | < 800ms |
| PDP detail | < 400ms |
| Auth login | < 300ms |
| Token refresh | < 100ms |
| Create order | < 1500ms |
| All other endpoints | < 500ms |

Concurrent users: 500 at launch.

---

## Tool: k6 (recommended)

```bash
npm install -g k6
# or: brew install k6 / apt install k6
```

---

## Test 1: PLP Load Test

```javascript
// k6/plp_load_test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '1m', target: 100 },   // ramp up to 100 VUs
    { duration: '3m', target: 500 },   // ramp up to 500 VUs
    { duration: '2m', target: 500 },   // hold at 500 VUs
    { duration: '1m', target: 0 },     // ramp down
  ],
  thresholds: {
    'http_req_duration{name:plp_cache_hit}': ['p(95)<300'],
    'http_req_duration{name:plp_cache_miss}': ['p(95)<800'],
    'http_req_failed': ['rate<0.01'],
  },
};

export default function () {
  const r = http.get('http://api.sabhyakriti.com/api/v1/products?page=1&sort=NEWEST', {
    tags: { name: 'plp_cache_hit' },
  });
  check(r, { 'status 200': (r) => r.status === 200 });
  sleep(1);
}
```

```bash
k6 run k6/plp_load_test.js
```

---

## Test 2: Checkout Flow Stress Test

```javascript
// k6/checkout_stress_test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 50,
  duration: '5m',
  thresholds: {
    'http_req_duration': ['p(95)<1500'],
    'http_req_failed': ['rate<0.02'],
  },
};

// Pre-populate: create test users and products before running
const BASE = 'http://api.sabhyakriti.com';

export default function () {
  // 1. Login
  const loginRes = http.post(`${BASE}/api/v1/auth/login`, JSON.stringify({
    email: `loadtest${__VU}@example.com`,
    password: 'LoadTest1!',
  }), { headers: { 'Content-Type': 'application/json' } });
  check(loginRes, { 'login 200': (r) => r.status === 200 });

  const token = loginRes.json('tokens.access_token');
  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };

  // 2. Add to cart
  http.post(`${BASE}/api/v1/cart/items`,
    JSON.stringify({ product_id: __ENV.TEST_PRODUCT_ID, quantity: 1 }), { headers });

  // 3. Create COD order
  const orderRes = http.post(`${BASE}/api/v1/orders`,
    JSON.stringify({ address_id: __ENV.TEST_ADDRESS_ID, payment_method: 'COD' }), { headers });
  check(orderRes, { 'order 201': (r) => r.status === 201 });

  sleep(2);
}
```

```bash
export TEST_PRODUCT_ID=<uuid>
export TEST_ADDRESS_ID=<uuid>
k6 run k6/checkout_stress_test.js
```

---

## Test 3: Auth Endpoint Rate Limiting Verification

```bash
# Verify rate limiting triggers at 10 req/min
for i in {1..12}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:8001/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"bad@test.com","password":"wrong"}'
done
# Expected: first 10 return 401, requests 11+ return 429
```

---

## Analyzing Results

```bash
# k6 outputs summary:
# ✓ http_req_duration p(95) = 245ms  (target <300ms — PASS)
# ✓ http_req_failed   rate  = 0.003  (target <0.01 — PASS)
```

If performance doesn't meet targets:
1. Check Redis cache hit rate (CloudWatch `PLPCacheHit` metric)
2. Check PostgreSQL slow queries (`pg_stat_statements`)
3. Review DB indexes (`EXPLAIN ANALYZE` on slow PLP queries)
4. Scale EC2 instance type (t3.large → c5.xlarge for product service)
5. Add Redis cluster for PLP cache at higher concurrency
