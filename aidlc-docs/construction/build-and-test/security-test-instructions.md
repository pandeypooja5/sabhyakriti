# Security Test Instructions — Sabhyakriti Platform

Security testing is MANDATORY per the Security Baseline Extension (SECURITY-01 to SECURITY-15).

---

## 1. Dependency Vulnerability Scanning (SECURITY-10)

### Python Services

```bash
# Install pip-audit
pip install pip-audit

# Run for each service
for svc in auth product cart order payment notification admin; do
  echo "==> Scanning sabhyakriti-${svc}-service..."
  cd C:/AI-Projects/sabhyakriti/sabhyakriti-${svc}-service
  pip-audit -r requirements.txt --strict
done
```

Expected: 0 high/critical vulnerabilities. Fix before deployment.

### Frontend

```bash
cd sabhyakriti-frontend
npm audit --audit-level=high
# Expected: 0 high/critical issues
```

---

## 2. HTTP Security Headers (SECURITY-04)

Run against each service's health endpoint:

```bash
curl -sI http://localhost:8001/health | grep -i \
  "strict-transport-security\|content-security-policy\|x-content-type-options\|x-frame-options\|referrer-policy\|cache-control"
```

Expected headers present:
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'none'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Cache-Control: no-store
```

---

## 3. Authentication & IDOR Tests (SECURITY-08)

```bash
# Test: accessing another user's order should return 403
USER_A_TOKEN="<user-a-token>"
USER_B_ORDER_ID="<order-belonging-to-user-b>"

curl -s -o /dev/null -w "%{http_code}\n" \
  http://localhost:8004/api/v1/orders/$USER_B_ORDER_ID \
  -H "Authorization: Bearer $USER_A_TOKEN"
# Expected: 403 (not 200 or 404)

# Test: unauthenticated access to protected endpoint
curl -s -o /dev/null -w "%{http_code}\n" \
  http://localhost:8004/api/v1/orders
# Expected: 401

# Test: customer JWT accessing admin endpoint
curl -s -o /dev/null -w "%{http_code}\n" \
  http://localhost:8007/api/v1/admin/dashboard \
  -H "Authorization: Bearer $USER_A_TOKEN"
# Expected: 403
```

---

## 4. Rate Limiting Verification (SECURITY-11)

```bash
# Auth login endpoint: max 10/min per IP
for i in {1..12}; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST http://localhost:8001/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}')
  echo "Request $i: HTTP $STATUS"
done
# Expected: requests 11-12 return 429 with Retry-After header
```

---

## 5. Razorpay Webhook Signature Verification (SECURITY-05)

```bash
# Send webhook with invalid signature → must return 400
curl -s -o /dev/null -w "%{http_code}\n" \
  -X POST http://localhost:8005/api/v1/payments/webhook \
  -H "Content-Type: application/json" \
  -H "X-Razorpay-Signature: invalidsignature123" \
  -d '{"event":"payment.captured"}'
# Expected: 400 (not 200)
```

---

## 6. Input Validation (SECURITY-05)

```bash
# SQL injection attempt in search
curl -s "http://localhost:8002/api/v1/products?search=' OR 1=1--" \
  -w "\nHTTP: %{http_code}\n"
# Expected: 200 with empty/normal results (no SQL error, no data leak)

# Oversized request body
curl -s -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"a@b.com\",\"password\":\"$(python3 -c 'print("x"*200)')\",\"full_name\":\"Test\"}" \
  -w "\nHTTP: %{http_code}\n"
# Expected: 422 (Pydantic validation — password max 128 chars)

# XSS in product description (admin)
# If description stored with bleach.clean, fetching should return stripped HTML
```

---

## 7. S3 Public Access Blocked (SECURITY-09)

```bash
# Direct S3 access must fail (only CloudFront OAC allowed)
curl -s -o /dev/null -w "%{http_code}\n" \
  "https://sabhyakriti-product-images.s3.ap-south-1.amazonaws.com/products/test.jpg"
# Expected: 403 AccessDenied

# CloudFront access should succeed
curl -s -o /dev/null -w "%{http_code}\n" \
  "https://cdn.sabhyakriti.com/products/test.jpg"
# Expected: 200 or 404 (not 403)
```

---

## 8. Internal Endpoint Protection (SECURITY-07)

```bash
# Internal endpoints must not be accessible without shared secret
curl -s -o /dev/null -w "%{http_code}\n" \
  http://localhost:8003/internal/v1/cart/{user-id}
# Expected: 401 or 403 (not 200)

# With wrong secret
curl -s -o /dev/null -w "%{http_code}\n" \
  http://localhost:8003/internal/v1/cart/{user-id} \
  -H "X-Internal-Secret: wrongsecret"
# Expected: 403
```

---

## 9. Static Analysis (SECURITY-05, SECURITY-10)

```bash
# Python: bandit security linter
pip install bandit
for svc in auth product cart order payment; do
  cd C:/AI-Projects/sabhyakriti/sabhyakriti-${svc}-service
  bandit -r . -x ./tests,./alembic -ll   # only high/medium severity
done

# Frontend: ESLint security plugin
cd sabhyakriti-frontend
npm run lint   # includes @typescript-eslint rules
```
