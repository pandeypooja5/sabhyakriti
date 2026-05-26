# Logical Components — Unit 1: Auth Microservice

---

## Component Map

```
HTTP Request
    |
    v
[ALB Health Check: GET /health]
[RateLimitMiddleware]         ← Redis sliding window
[RequestLoggingMiddleware]    ← structlog JSON to CloudWatch
[JWTAuthMiddleware]          ← RS256 validation (protected routes only)
[SecurityHeadersMiddleware]   ← HSTS, CSP, X-Frame-Options, etc.
[CORSMiddleware]              ← Frontend domain allow-list
    |
    v
[FastAPI Routers]
    AuthRouter   /api/v1/auth/*
    UsersRouter  /api/v1/users/me
    JWKSRouter   /auth/.well-known/jwks.json
    HealthRouter /health
    |
    v
[Application Services]
    AuthApplicationService
    |
    +---> [Domain Services — none for auth]
    |
    +---> [Repository Interfaces]
    |         IUserRepository
    |         IRefreshTokenRepository  (Redis)
    |         IOTPRepository           (Redis + DB)
    |         IEmailVerificationTokenRepository
    |         IPasswordResetTokenRepository
    |
    +---> [External Adapters]
              GoogleOAuthAdapter
              FacebookOAuthAdapter
              TwilioSMSAdapter
              AWSSESAdapter
              HIBPAdapter
              AWSSecretsManagerAdapter
    |
    v
[Infrastructure]
    SQLAlchemyUserRepository         ← PostgreSQL (auth schema)
    RedisTokenRepository             ← ElastiCache Redis
    SQLAlchemyOTPRepository          ← PostgreSQL (with Redis cache)
    SQLAlchemyVerificationRepository ← PostgreSQL
```

---

## Logical Component Inventory

### Middleware Stack (ordered — outermost first)

| Component | Type | Responsibility |
|---|---|---|
| `CORSMiddleware` | FastAPI middleware | Allow-list: `https://sabhyakriti.com`, `https://www.sabhyakriti.com` only |
| `SecurityHeadersMiddleware` | Custom FastAPI middleware | Inject HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Cache-Control: no-store |
| `RequestLoggingMiddleware` | Custom FastAPI middleware | Generate `request_id` (UUID), log request start/end with latency; attach `request_id` to response header |
| `RateLimitMiddleware` | Custom FastAPI middleware | Redis sliding window per endpoint+IP; skip if Redis unavailable (fail-open) |
| `GlobalExceptionHandler` | FastAPI exception handler | Catch all unhandled exceptions; log with stack trace; return generic 500 |

### Routers

| Router | Prefix | Auth Required | Routes |
|---|---|---|---|
| `AuthRouter` | `/api/v1/auth` | No (public) | POST /register, POST /login, POST /refresh, POST /logout, POST /logout-all, POST /otp/send, POST /otp/verify, GET /oauth/{provider}/init, GET /oauth/{provider}/callback, POST /verify-email, POST /verify-email/resend, POST /forgot-password, POST /reset-password |
| `AdminAuthRouter` | `/api/v1/auth/admin` | MFA pending token | POST /mfa/setup, POST /mfa/verify, POST /mfa/confirm-setup |
| `UsersRouter` | `/api/v1/users` | JWT required | GET /me, PATCH /me, POST /me/change-password |
| `JWKSRouter` | `/auth/.well-known` | No (public) | GET /jwks.json |
| `HealthRouter` | `/` | No | GET /health |

### Application Service

| Component | Pattern | Responsibility |
|---|---|---|
| `AuthApplicationService` | Application Service (DDD) | Orchestrates all 12 auth flows; coordinates repositories and adapters |
| `PasswordHasher` | Singleton (startup) | Argon2id hash + verify; injected via FastAPI `Depends` |
| `JWTService` | Singleton (startup) | RS256 sign + decode; private key loaded from Secrets Manager at startup |
| `AESEncryptionService` | Singleton (startup) | AES-256-GCM encrypt/decrypt for TOTP secrets |
| `TOTPService` | Stateless | Generate TOTP secret, provisioning URI, verify code with replay prevention |
| `OAuthService` | Stateless | Handles Google + Facebook PKCE flows via `authlib` |

### Repository Implementations

| Component | Backed By | Key Operations |
|---|---|---|
| `SQLAlchemyUserRepository` | PostgreSQL `auth.users` | find_by_email, find_by_phone, find_by_id, create, update, save |
| `SQLAlchemyOAuthAccountRepository` | PostgreSQL `auth.oauth_accounts` | find_by_provider, create, link_to_user |
| `RedisTokenRepository` | ElastiCache Redis | store_refresh_token, find_refresh_token, revoke_token, revoke_all_for_user |
| `RedisOTPRepository` | ElastiCache Redis | store_otp, find_otp, increment_attempts, invalidate |
| `SQLAlchemyEmailVerificationRepository` | PostgreSQL `auth.email_verification_tokens` | create, find_by_hash, mark_used |
| `SQLAlchemyPasswordResetRepository` | PostgreSQL `auth.password_reset_tokens` | create, find_by_hash, invalidate_existing, mark_used |

### External Adapters

| Component | Wraps | Key Methods |
|---|---|---|
| `GoogleOAuthAdapter` | Google Identity API | `get_auth_url(state, pkce)`, `exchange_code(code, verifier)`, `get_user_profile(access_token)` |
| `FacebookOAuthAdapter` | Facebook Graph API | `get_auth_url(state)`, `exchange_code(code)`, `get_user_profile(access_token)` |
| `TwilioSMSAdapter` | Twilio REST API | `send_otp(phone, otp_code)` with retry via tenacity |
| `AWSSESAdapter` | boto3 SES | `send_verification_email(to, link)`, `send_password_reset_email(to, link)` with retry |
| `HIBPAdapter` | HIBP k-anonymity API | `is_password_breached(password)` → bool; fail-open on timeout |
| `AWSSecretsManagerAdapter` | boto3 SecretsManager | `get_secret(name)` → str; called once at startup |

---

## Infrastructure Components

| Component | AWS Service | Config |
|---|---|---|
| Compute | EC2 t3.medium | 1 instance, private subnet, Docker container |
| Load balancer entry | ALB (shared, Unit 8) | Path: `/api/v1/auth/*`, `/auth/.well-known/*`, `/health` → port 8001 |
| Database | RDS PostgreSQL 15 | Multi-AZ, `auth` schema, `db.t3.micro` (single micro for MVP) |
| Token cache | ElastiCache Redis | cache.t3.micro, single node, `allkeys-lru` |
| Secrets | AWS Secrets Manager | `sabhyakriti/auth/jwt-private-key`, `sabhyakriti/auth/aes-key`, `sabhyakriti/auth/db-password` |
| Logs | CloudWatch Logs | Log group: `/sabhyakriti/auth-service`, retention: 90 days |
| Metrics | CloudWatch Metrics | Custom namespace: `Sabhyakriti/Auth`; metrics: LoginSuccess, LoginFailure, OTPSent, RegistrationCount |
| Container registry | ECR | `sabhyakriti/auth-service:latest` → pinned digest in production |
