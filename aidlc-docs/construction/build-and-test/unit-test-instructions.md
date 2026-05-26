# Unit Test Execution Instructions — Sabhyakriti Platform

---

## Backend Services (Python/pytest)

Run unit tests for **each** service. Tests use `pytest` with `fakeredis` and `unittest.mock` — no live DB or external APIs required.

### Run All Unit Tests (per service)

```bash
cd sabhyakriti-{service-name}
source .venv/bin/activate
pytest tests/ -v --cov=. --cov-fail-under=80 --cov-report=term-missing
```

### Run Specific Test Categories

```bash
# Domain tests only (no DB/Redis required — fastest)
pytest tests/domain/ -v

# Application service tests (mocked repos)
pytest tests/application/ -v

# Infrastructure tests (uses fakeredis + in-memory SQLite where applicable)
pytest tests/infrastructure/ -v
```

### Expected Results per Service

| Service | Test Files | Min Coverage |
|---|---|---|
| auth-service | 9 test files, ~60 tests | 80% |
| product-service | 7 test files, ~45 tests | 80% |
| cart-service | 5 test files, ~40 tests | 80% |
| order-service | 5 test files, ~35 tests | 80% |
| payment-service | 4 test files, ~40 tests | 80% |
| notification-service | 3 test files, ~50 tests | 80% |
| admin-service | 3 test files, ~15 tests | 80% |

### Property-Based Tests (Hypothesis)

Hypothesis runs automatically within `pytest`. To run PBT suites specifically:

```bash
# Auth service: password hashing, phone number validation
pytest tests/domain/test_value_objects.py -v -x

# Product service: pricing formula, slug generation, stock status
pytest tests/domain/test_pricing_service.py tests/domain/test_slug_service.py -v

# Cart service: totals calculation, coupon discount
pytest tests/domain/test_pricing_service.py -v

# Payment service: HMAC signature roundtrip
pytest tests/domain/test_signature_service.py -v

# Order service: refund amount calculation
pytest tests/domain/test_order_domain_service.py -v
```

---

## AWS Infrastructure (CDK Assertions)

```bash
cd sabhyakriti-infra
source .venv/bin/activate
pytest tests/ -v
```

Expected: ~10 tests covering VPC CIDR, NAT count, security groups, S3 public-access-blocked, CloudFront HTTPS-only.

---

## Frontend (Vitest)

```bash
cd sabhyakriti-frontend
npm run test               # run all tests
npm run test -- --coverage # with coverage report
```

Expected: ~15 tests covering:
- `formatINR` currency formatting edge cases
- Indian phone / pincode validation
- `ProductCard` renders correctly
- `CartSummary` GST = 5% of net amount
- `CouponInput` apply/remove behaviour

---

## Run All Unit Tests Sequentially (convenience script)

```bash
#!/usr/bin/env bash
SERVICES=(auth product cart order payment notification admin)
for svc in "${SERVICES[@]}"; do
  echo "==> Testing sabhyakriti-${svc}-service..."
  cd "C:/AI-Projects/sabhyakriti/sabhyakriti-${svc}-service"
  pytest tests/ -q --tb=short --cov=. --cov-fail-under=80
  echo ""
done

echo "==> Testing frontend..."
cd "C:/AI-Projects/sabhyakriti/sabhyakriti-frontend"
npm run test -- --run

echo "==> Testing CDK infra..."
cd "C:/AI-Projects/sabhyakriti/sabhyakriti-infra"
pytest tests/ -q
```

---

## Fixing Failing Tests

1. Run with verbose output: `pytest tests/ -v -x --tb=long`
2. For Hypothesis failures: `pytest --hypothesis-seed=0` for reproducible runs
3. For coverage below 80%: add tests for uncovered lines shown in `--cov-report=term-missing`
4. For frontend: `npm run test -- --reporter=verbose`
