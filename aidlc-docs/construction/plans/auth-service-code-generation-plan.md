# Code Generation Plan — Unit 1: Auth Microservice
# sabhyakriti-auth-service

---

## Unit Context

| Field | Value |
|---|---|
| **Repository** | `sabhyakriti-auth-service` (separate repo) |
| **Code location** | `C:\AI-Projects\sabhyakriti\sabhyakriti-auth-service\` |
| **Pattern** | Greenfield multi-unit microservice → `{unit-name}/` at workspace root |
| **Runtime** | Python 3.11 + FastAPI + SQLAlchemy 2.0 (async) |
| **Requirements covered** | FR-AUTH-01 to FR-AUTH-10, FR-ACC-01, NFR-SEC-12, NFR-AUTH-* |

---

## Generation Steps

### Step 1: Project Structure Setup
- [x] 1.1 Create repository root `sabhyakriti-auth-service/`
- [x] 1.2 Create `pyproject.toml` (project metadata, dependencies, tool config)
- [x] 1.3 Create `requirements.txt` (pinned production deps)
- [x] 1.4 Create `requirements-dev.txt` (test + lint deps)
- [x] 1.5 Create `.env.example` (all required env vars documented, no values)
- [x] 1.6 Create `Dockerfile` (non-root user, pinned base image, healthcheck)
- [x] 1.7 Create `docker-compose.dev.yml` (local dev with PostgreSQL + Redis)
- [x] 1.8 Create `.github/workflows/auth-service.yml` (CI/CD pipeline)
- [x] 1.9 Create directory tree: `domain/`, `application/`, `infrastructure/`, `presentation/`, `tests/`, `alembic/`

### Step 2: Domain Layer — Entities & Value Objects
- [x] 2.1 `domain/entities/user.py` — User dataclass/entity (no ORM, pure Python)
- [x] 2.2 `domain/entities/oauth_account.py`
- [x] 2.3 `domain/entities/tokens.py` — RefreshToken, EmailVerificationToken, PasswordResetToken
- [x] 2.4 `domain/entities/otp_record.py`
- [x] 2.5 `domain/value_objects.py` — UserRole, OAuthProvider, TokenPair, IndianPhoneNumber
- [x] 2.6 `domain/repositories/i_user_repository.py` — abstract interface
- [x] 2.7 `domain/repositories/i_token_repository.py` — abstract interface
- [x] 2.8 `domain/repositories/i_otp_repository.py` — abstract interface
- [x] 2.9 `domain/repositories/i_verification_repository.py` — abstract interface

### Step 3: Domain Layer — Unit Tests
- [x] 3.1 `tests/domain/test_value_objects.py` — IndianPhoneNumber validation, UserRole enum
- [x] 3.2 `tests/domain/test_entities.py` — User entity construction, OTPRecord attempt logic

### Step 4: Application Layer — Services
- [x] 4.1 `application/services/password_hasher.py` — Argon2id wrapper singleton
- [x] 4.2 `application/services/jwt_service.py` — RS256 sign/decode, JWK set endpoint data
- [x] 4.3 `application/services/aes_encryption_service.py` — AES-256-GCM for TOTP secrets
- [x] 4.4 `application/services/totp_service.py` — pyotp wrapper; generate secret, verify code, replay prevention
- [x] 4.5 `application/services/oauth_service.py` — authlib PKCE flows for Google + Facebook
- [x] 4.6 `application/dtos/auth_dtos.py` — Pydantic v2 request/response schemas (RegisterRequest, LoginRequest, TokenPairResponse, UserProfileResponse, …)
- [x] 4.7 `application/services/auth_application_service.py` — all 12 business flows (registration, login, OAuth, OTP send/verify, refresh, logout, MFA, password change/reset)

### Step 5: Application Layer — Unit Tests
- [x] 5.1 `tests/application/test_auth_service_register.py` — registration flow + HIBP check + duplicate email
- [x] 5.2 `tests/application/test_auth_service_login.py` — login success, wrong password, lockout, unverified email
- [x] 5.3 `tests/application/test_auth_service_oauth.py` — Google/Facebook auto-link, new user creation
- [x] 5.4 `tests/application/test_auth_service_otp.py` — OTP send/verify, attempt limits, cooldown
- [x] 5.5 `tests/application/test_auth_service_tokens.py` — refresh, rotation, revocation, password change invalidation
- [x] 5.6 `tests/application/test_auth_service_mfa.py` — MFA setup, TOTP verify, replay prevention
- [x] 5.7 `tests/application/test_password_hasher.py` + PBT with Hypothesis (password boundary values)

### Step 6: Infrastructure Layer — DB Models & Repositories
- [x] 6.1 `infrastructure/persistence/models.py` — SQLAlchemy ORM models (UserModel, OAuthAccountModel, EmailVerificationTokenModel, PasswordResetTokenModel) in `auth` schema
- [x] 6.2 `infrastructure/persistence/database.py` — async engine, session factory, connection pool config
- [x] 6.3 `infrastructure/persistence/repositories/sqlalchemy_user_repository.py`
- [x] 6.4 `infrastructure/persistence/repositories/sqlalchemy_oauth_repository.py`
- [x] 6.5 `infrastructure/persistence/repositories/sqlalchemy_verification_repository.py`
- [x] 6.6 `infrastructure/persistence/repositories/sqlalchemy_reset_repository.py`
- [x] 6.7 `infrastructure/cache/redis_token_repository.py` — refresh token store (SHA-256, TTL, Lua bulk-revoke)
- [x] 6.8 `infrastructure/cache/redis_otp_repository.py` — OTP store with attempt counter
- [x] 6.9 `infrastructure/cache/redis_rate_limiter.py` — sliding window Lua script
- [x] 6.10 `alembic/versions/0001_create_auth_schema.py` — migration: create auth schema + all tables + indexes

### Step 7: Infrastructure Layer — Unit Tests
- [x] 7.1 `tests/infrastructure/test_sqlalchemy_user_repository.py` — CRUD against real test PostgreSQL
- [x] 7.2 `tests/infrastructure/test_redis_token_repository.py` — store, lookup, revoke against real test Redis
- [x] 7.3 `tests/infrastructure/test_redis_rate_limiter.py` — sliding window boundary behaviour (PBT with Hypothesis)

### Step 8: Infrastructure Layer — External Adapters
- [x] 8.1 `infrastructure/adapters/google_oauth_adapter.py` — authlib PKCE; state + code exchange; profile fetch
- [x] 8.2 `infrastructure/adapters/facebook_oauth_adapter.py`
- [x] 8.3 `infrastructure/adapters/twilio_sms_adapter.py` — send OTP with tenacity retry
- [x] 8.4 `infrastructure/adapters/aws_ses_adapter.py` — send email with tenacity retry
- [x] 8.5 `infrastructure/adapters/hibp_adapter.py` — k-anonymity check; fail-open on timeout
- [x] 8.6 `infrastructure/adapters/aws_secrets_adapter.py` — load secrets at startup

### Step 9: Adapter Unit Tests
- [x] 9.1 `tests/infrastructure/test_twilio_adapter.py` — mock Twilio SDK; retry behaviour
- [x] 9.2 `tests/infrastructure/test_ses_adapter.py` — mock boto3 SES; retry behaviour
- [x] 9.3 `tests/infrastructure/test_hibp_adapter.py` — mock httpx; timeout → fail-open

### Step 10: Presentation Layer — FastAPI App
- [x] 10.1 `presentation/middleware/security_headers.py`
- [x] 10.2 `presentation/middleware/request_logging.py` — structlog JSON; request_id injection
- [x] 10.3 `presentation/middleware/rate_limit.py` — delegates to RedisRateLimiter
- [x] 10.4 `presentation/middleware/global_exception_handler.py`
- [x] 10.5 `presentation/dependencies.py` — `get_db()`, `get_redis()`, `get_current_user()`, `require_admin()`
- [x] 10.6 `presentation/routers/auth_router.py` — all `/api/v1/auth/*` endpoints (register, login, OAuth, OTP, email-verify, forgot/reset password, logout)
- [x] 10.7 `presentation/routers/admin_auth_router.py` — MFA setup + verify endpoints
- [x] 10.8 `presentation/routers/users_router.py` — `/api/v1/users/me` profile + change-password
- [x] 10.9 `presentation/routers/jwks_router.py` — `/.well-known/jwks.json`
- [x] 10.10 `presentation/routers/health_router.py` — `/health` with DB + Redis status
- [x] 10.11 `main.py` — FastAPI app factory; lifespan (startup secrets load); middleware registration; router inclusion

### Step 11: Integration Tests (API Layer)
- [x] 11.1 `tests/integration/test_register_login_flow.py` — full register → verify email → login → refresh → logout
- [x] 11.2 `tests/integration/test_oauth_flow.py` — mock OAuth provider; auto-link existing account
- [x] 11.3 `tests/integration/test_otp_flow.py` — send OTP → verify → get tokens; attempt limit; cooldown
- [x] 11.4 `tests/integration/test_lockout_flow.py` — 5 failed logins → 423; auto-unlock after 15 min
- [x] 11.5 `tests/integration/test_mfa_flow.py` — admin login → MFA pending → TOTP verify → full tokens
- [x] 11.6 `tests/integration/test_password_reset_flow.py` — request reset → use token → login with new password
- [x] 11.7 `tests/integration/test_rate_limiting.py` — exceed rate limit → 429 with Retry-After header
- [x] 11.8 `tests/conftest.py` — pytest fixtures: async test client, test DB session, test Redis, factory-boy factories

### Step 12: Documentation & Deployment Artifacts
- [x] 12.1 `aidlc-docs/construction/auth-service/code/code-summary.md` — list of all created files with purpose
- [x] 12.2 `README.md` — local setup instructions, env vars reference, how to run tests

---

## Story Traceability

| Story / Req ID | Implemented In Step |
|---|---|
| FR-AUTH-01 (email registration) | 4.7, 10.6 |
| FR-AUTH-02 (email login) | 4.7, 10.6 |
| FR-AUTH-03 (Google OAuth) | 4.5, 8.1, 10.6 |
| FR-AUTH-04 (Facebook OAuth) | 4.5, 8.2, 10.6 |
| FR-AUTH-05 (Phone OTP) | 4.7, 8.3, 10.6 |
| FR-AUTH-06 (Password reset) | 4.7, 8.4, 10.6 |
| FR-AUTH-07 (Email verification) | 4.7, 8.4, 10.6 |
| FR-AUTH-08 (JWT sessions) | 4.2, 6.7, 10.6 |
| FR-AUTH-09 (Logout + revoke) | 4.7, 6.7, 10.6 |
| FR-AUTH-10 (Admin MFA) | 4.3, 4.4, 10.7 |
| FR-ACC-01 (User profile) | 4.7, 10.8 |
| SECURITY-12 (Auth hardening) | 4.1, 4.2, 4.7, 6.8, 6.9 |

---

## Total: 12 steps, 55 sub-tasks
