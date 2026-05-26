# NFR Requirements — Unit 1: Auth Microservice

---

## 1. Performance Requirements

| ID | Requirement | Target |
|---|---|---|
| NFR-AUTH-PERF-01 | Login endpoint (POST /auth/login) p95 response time | < 300ms |
| NFR-AUTH-PERF-02 | Registration endpoint p95 response time | < 400ms (includes HIBP check) |
| NFR-AUTH-PERF-03 | Token refresh endpoint p95 response time | < 100ms (Redis lookup) |
| NFR-AUTH-PERF-04 | OTP verification p95 response time | < 200ms |
| NFR-AUTH-PERF-05 | All other auth endpoints p95 response time | < 500ms (NFR-PERF-04) |
| NFR-AUTH-PERF-06 | HIBP API call timeout | 2 seconds max; fail open if unreachable (log warning, do not block registration) |
| NFR-AUTH-PERF-07 | Argon2id hash time | Tuned to ~200–300ms on t3.medium hardware |

---

## 2. Scalability Requirements

| ID | Requirement | Value |
|---|---|---|
| NFR-AUTH-SCAL-01 | Peak concurrent users at launch | 500 |
| NFR-AUTH-SCAL-02 | EC2 instance type | t3.medium (2 vCPU, 4 GB RAM) |
| NFR-AUTH-SCAL-03 | FastAPI worker processes | 2 Uvicorn workers × 4 async workers per process |
| NFR-AUTH-SCAL-04 | Redis instance | AWS ElastiCache — single cache.t3.micro node |
| NFR-AUTH-SCAL-05 | Auto Scaling | Disabled for MVP; manual scale-up if needed |
| NFR-AUTH-SCAL-06 | Max Redis memory | 512 MB; eviction policy: `allkeys-lru` |
| NFR-AUTH-SCAL-07 | Database connections | SQLAlchemy pool: min=2, max=10, overflow=5 |

---

## 3. Availability Requirements

| ID | Requirement | Value |
|---|---|---|
| NFR-AUTH-AVAIL-01 | Uptime SLA | 99.9% (≤ 8.7 hours downtime/year) |
| NFR-AUTH-AVAIL-02 | RDS deployment | Multi-AZ enabled — automatic failover ~60s if primary fails |
| NFR-AUTH-AVAIL-03 | Redis deployment | Single node (MVP); Redis outage causes users to need re-login (acceptable per Q2) |
| NFR-AUTH-AVAIL-04 | EC2 health check | ALB health check every 30s on `/health` endpoint |
| NFR-AUTH-AVAIL-05 | Graceful shutdown | SIGTERM handler — drain in-flight requests (max 30s) before shutdown |
| NFR-AUTH-AVAIL-06 | RTO | 5 minutes (EC2 replacement via Auto Scaling launch template) |
| NFR-AUTH-AVAIL-07 | RPO | Near-zero for DB (Multi-AZ sync replication); up to Redis TTL for token data |

---

## 4. Security Requirements

All SECURITY-01 through SECURITY-15 rules enforced. Auth-specific highlights:

| ID | Requirement |
|---|---|
| NFR-AUTH-SEC-01 | Argon2id password hashing (SECURITY-12) |
| NFR-AUTH-SEC-02 | RS256 JWT with private key in AWS Secrets Manager; public key exposed at `/auth/.well-known/jwks.json` |
| NFR-AUTH-SEC-03 | Redis refresh tokens stored as SHA-256 hashes — never plaintext (SECURITY-12) |
| NFR-AUTH-SEC-04 | Rate limiting on all auth endpoints via Redis sliding window (SECURITY-11) |
| NFR-AUTH-SEC-05 | AES-256-GCM encryption for TOTP secrets; key from AWS Secrets Manager (SECURITY-12) |
| NFR-AUTH-SEC-06 | All DB connections use TLS (RDS enforce_ssl=true) (SECURITY-01) |
| NFR-AUTH-SEC-07 | No secrets in environment variables or code — all from AWS Secrets Manager (SECURITY-12) |
| NFR-AUTH-SEC-08 | HTTP security headers on all responses (SECURITY-04) |
| NFR-AUTH-SEC-09 | CORS restricted to frontend domain only (SECURITY-08) |
| NFR-AUTH-SEC-10 | CloudWatch structured logging — no PII in logs (SECURITY-03) |
| NFR-AUTH-SEC-11 | Global exception handler returns generic 500 — no stack traces to client (SECURITY-15) |

---

## 5. Reliability Requirements

| ID | Requirement |
|---|---|
| NFR-AUTH-REL-01 | External call retry: HIBP API — 1 retry with 500ms backoff; fail open on timeout |
| NFR-AUTH-REL-02 | External call retry: Twilio SMS — 2 retries with exponential backoff (1s, 2s); log failure to CloudWatch; return 503 to user if all retries fail |
| NFR-AUTH-REL-03 | External call retry: AWS SES email — 2 retries; email failure must not block login/registration response |
| NFR-AUTH-REL-04 | All DB operations wrapped in try/finally — connection returned to pool on error |
| NFR-AUTH-REL-05 | Redis connection failure → fallback: rate limiting disabled (fail open), log alert to CloudWatch |
| NFR-AUTH-REL-06 | Unhandled exceptions caught by global handler — logged with correlation ID, return HTTP 500 |

---

## 6. Maintainability & Testability Requirements

| ID | Requirement |
|---|---|
| NFR-AUTH-MAINT-01 | Minimum test coverage: **80% line coverage** (enforced in CI via `pytest --cov`) |
| NFR-AUTH-MAINT-02 | Property-based tests (Hypothesis) for: password validation logic, token TTL calculations, phone number normalization, OTP attempt counter boundaries |
| NFR-AUTH-MAINT-03 | All FastAPI endpoints covered by integration tests using `httpx.AsyncClient` |
| NFR-AUTH-MAINT-04 | All external adapters (Twilio, SES, HIBP, OAuth) must be mockable via dependency injection |
| NFR-AUTH-MAINT-05 | Structured logging: every request logs `request_id`, `user_id` (if available), `endpoint`, `status_code`, `latency_ms` |
| NFR-AUTH-MAINT-06 | Full type hints throughout (mypy strict mode in CI) |
| NFR-AUTH-MAINT-07 | Alembic migrations for all schema changes — no manual SQL in production |
