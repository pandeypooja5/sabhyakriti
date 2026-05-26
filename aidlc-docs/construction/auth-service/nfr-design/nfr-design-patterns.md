# NFR Design Patterns — Unit 1: Auth Microservice

---

## 1. Security Patterns

### 1.1 Credential Storage Pattern
- **Pattern**: Adaptive hashing with Argon2id
- **Application**: All password and OTP storage
- **Design**: `passlib` CryptContext configured with Argon2id (memory=65536, time_cost=3, parallelism=2). Single `PasswordHasher` singleton injected via FastAPI dependency.
- **SECURITY rule**: SECURITY-12

### 1.2 JWT Asymmetric Key Pattern
- **Pattern**: RS256 public/private key pair
- **Application**: Access token signing and verification
- **Design**:
  - Private key (PEM) stored in AWS Secrets Manager; loaded once at startup into memory
  - Public key exposed at `GET /auth/.well-known/jwks.json` (JWK Set format)
  - All other microservices fetch the public key once at startup and cache it
  - Token rotation: new refresh token issued on every access token refresh
- **SECURITY rule**: SECURITY-12, SECURITY-08

### 1.3 Token Revocation Pattern
- **Pattern**: Redis-backed allowlist with SHA-256 hashing
- **Application**: Refresh token validation and revocation
- **Design**:
  - Key: `refresh:{user_id}:{jti}` → value: `{ revoked: false, expires_at: unix_ts }`
  - On logout: set `revoked: true` (preserve for audit) or `DEL` the key
  - On password change: `SCAN` + `DEL` all `refresh:{user_id}:*` keys atomically via Lua script
  - TTL on Redis keys matches token `exp`; Redis handles expiry automatically
- **SECURITY rule**: SECURITY-12

### 1.4 Rate Limiting Pattern
- **Pattern**: Redis sliding window counter
- **Application**: Login, registration, OTP send, password reset endpoints
- **Design**:
  - Key: `ratelimit:{endpoint}:{ip}` → sorted set of request timestamps
  - On each request: ZADD current timestamp; ZREMRANGEBYSCORE (remove old entries outside window); ZCARD for count
  - Single Lua script for atomicity (ZADD + ZREMRANGEBYSCORE + ZCARD + EXPIRE)
  - If count > limit: return 429 with `Retry-After` header
- **SECURITY rule**: SECURITY-11

### 1.5 HTTP Security Headers Pattern
- **Pattern**: Middleware-applied response headers
- **Application**: All HTTP responses from the Auth Service
- **Design**: `SecurityHeadersMiddleware` (FastAPI middleware) appends on every response:

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'none'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Cache-Control: no-store  (auth responses must not be cached)
```
- **SECURITY rule**: SECURITY-04

### 1.6 CSRF Protection Pattern (OAuth)
- **Pattern**: State parameter with Redis-backed nonce
- **Application**: Google and Facebook OAuth initiation and callback
- **Design**:
  - On OAuth initiate: generate 32-byte random `state`; store in Redis `oauth_state:{state}` with 10min TTL
  - On callback: verify `state` param exists in Redis; delete immediately after verification
  - PKCE: generate `code_verifier` (43–128 char random); send `code_challenge` (S256) in auth request

---

## 2. Resilience Patterns

### 2.1 Retry with Timeout Pattern
- **Application**: HIBP API, Twilio SMS, AWS SES
- **Design**:

| External Service | Retries | Backoff | Timeout | Failure Behaviour |
|---|---|---|---|---|
| HIBP API | 1 retry | 500ms fixed | 2s | Fail open — log warning, allow registration |
| Twilio SMS | 2 retries | Exponential 1s, 2s | 5s | Fail closed — return 503 to user, log alert |
| AWS SES | 2 retries | Exponential 1s, 2s | 5s | Fail open for non-critical emails (verification, reset sent async) |

- **Implementation**: `tenacity` library with `retry`, `stop`, `wait` decorators on adapter methods

### 2.2 Fail-Safe Default Pattern
- **Application**: Redis unavailability
- **Design**:
  - Rate limiting: Redis down → skip rate limiting, log CRITICAL alert to CloudWatch (fail open — prioritise availability over strict rate limiting for MVP)
  - Token validation: Redis down → attempt DB fallback for refresh token lookup; if DB also unavailable → 503
- **SECURITY rule**: SECURITY-15

### 2.3 Global Exception Handler Pattern
- **Application**: All unhandled exceptions in FastAPI
- **Design**:
  - `@app.exception_handler(Exception)`: catch all → log with `structlog` including `request_id`, stack trace → return `{ "detail": "An unexpected error occurred", "request_id": "..." }` with HTTP 500
  - Never expose exception message, stack trace, or internal paths to the client
- **SECURITY rule**: SECURITY-15, SECURITY-09

---

## 3. Performance Patterns

### 3.1 Connection Pool Pattern
- **Application**: PostgreSQL connections
- **Design**: SQLAlchemy async engine with `pool_size=2, max_overflow=5, pool_timeout=10, pool_pre_ping=True`
- **Rationale**: t3.medium with 500 concurrent users; auth DB operations are short-lived

### 3.2 Startup Secrets Loading Pattern
- **Application**: JWT private key, AES encryption key
- **Design**: Load from AWS Secrets Manager once on `startup` FastAPI lifespan event → store in module-level singletons → never reload during request handling
- **Rationale**: Eliminates per-request Secrets Manager API calls (latency + cost)

### 3.3 Structured Logging Pattern
- **Application**: All request/response logging
- **Design**: `structlog` configured with JSON renderer → output to stdout → captured by Docker log driver → forwarded to CloudWatch Logs
- **Log fields**: `timestamp`, `level`, `request_id`, `method`, `path`, `status_code`, `latency_ms`, `user_id` (if authenticated)
- **PII rule**: Never log `password`, `otp_code`, `token` values — only log `user_id`, `email_domain` (not full email)
- **SECURITY rule**: SECURITY-03
