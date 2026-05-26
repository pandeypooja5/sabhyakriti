# NFR Requirements — Unit 2: Product Microservice

---

## 1. Performance

| ID | Requirement | Target |
|---|---|---|
| NFR-PROD-PERF-01 | PLP list endpoint p95 (no cache miss) | < 300ms |
| NFR-PROD-PERF-02 | PLP list endpoint p95 (cache miss — DB query) | < 800ms |
| NFR-PROD-PERF-03 | PDP detail endpoint p95 | < 400ms |
| NFR-PROD-PERF-04 | Related products fetch | < 150ms |
| NFR-PROD-PERF-05 | All other endpoints p95 | < 500ms |
| NFR-PROD-PERF-06 | Full-text search (tsvector) uses GIN index — query planner uses index scan |
| NFR-PROD-PERF-07 | PLP Redis cache TTL = 5 minutes; key = SHA-256 of (filter_hash + sort + page + page_size) |
| NFR-PROD-PERF-08 | Cache invalidated on any product create/update/delete and category change |

## 2. Scalability

| ID | Requirement | Value |
|---|---|---|
| NFR-PROD-SCAL-01 | EC2 instance | t3.large (2 vCPU, 8 GB RAM) — larger than Auth due to heavier read load |
| NFR-PROD-SCAL-02 | Uvicorn workers | 4 workers × 4 async coroutines |
| NFR-PROD-SCAL-03 | DB connection pool | pool_size=5, max_overflow=10 |
| NFR-PROD-SCAL-04 | PostgreSQL read replica | All customer PLP/PDP queries route to read replica; writes go to primary |
| NFR-PROD-SCAL-05 | Redis (shared with Auth Service) | Separate DB index: Redis DB 1 for product cache |

## 3. Availability

| ID | Requirement | Value |
|---|---|---|
| NFR-PROD-AVAIL-01 | Uptime SLA | 99.9% |
| NFR-PROD-AVAIL-02 | RDS read replica | All read queries; primary only for writes |
| NFR-PROD-AVAIL-03 | Redis unavailable | Fall through to DB; log alert; do NOT return 5xx |
| NFR-PROD-AVAIL-04 | Order Service unavailable (review verified-purchase check) | Proceed with `is_verified_purchase=False`; do NOT block review creation if Order Service is unreachable |

## 4. Security

SECURITY-01 through SECURITY-15 fully enforced. Product-specific:

| ID | Requirement |
|---|---|
| NFR-PROD-SEC-01 | S3 bucket: block all public access; only CloudFront + presigned URLs allowed |
| NFR-PROD-SEC-02 | Presigned URL TTL = 15 min; content-type header restricted to image types only |
| NFR-PROD-SEC-03 | Internal stock endpoint (`/internal/v1/products/{id}/stock`) requires shared secret header — NOT exposed via public ALB |
| NFR-PROD-SEC-04 | CSV upload: validate file MIME type + max 2 MB size before processing |
| NFR-PROD-SEC-05 | Admin endpoints: JWT validation + ADMIN role check on every request |
| NFR-PROD-SEC-06 | Product descriptions sanitised to strip HTML/script before storage (XSS prevention) |

## 5. Testability

| ID | Requirement |
|---|---|
| NFR-PROD-TEST-01 | Minimum 80% line coverage |
| NFR-PROD-TEST-02 | PBT (Hypothesis) for: pricing formula (discount_percentage boundaries 0, 100, fractional), slug generation (unicode/special chars), pagination boundary values, filter logic combinations |
| NFR-PROD-TEST-03 | Integration tests for PLP filter combinations using real PostgreSQL |
| NFR-PROD-TEST-04 | All S3 adapter calls mockable via dependency injection |
| NFR-PROD-TEST-05 | Order Service client mockable; test both reachable (True/False) and unreachable scenarios |
