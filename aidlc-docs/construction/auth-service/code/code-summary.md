# Code Summary — Unit 1: Auth Microservice

All files generated under `sabhyakriti-auth-service/`.

## Project Setup (Step 1)
- `pyproject.toml` — project config, ruff/mypy/pytest settings, 80% coverage gate
- `requirements.txt` — pinned production dependencies
- `requirements-dev.txt` — test + lint dependencies
- `.env.example` — all required environment variables documented
- `Dockerfile` — python:3.11-slim, non-root user, healthcheck, 2 Uvicorn workers
- `docker-compose.dev.yml` — local dev with PostgreSQL 15 + Redis 7
- `.github/workflows/auth-service.yml` — CI: lint → type-check → test → build → ECR push → EC2 deploy

## Domain Layer (Step 2)
- `domain/value_objects.py` — UserRole, OAuthProvider, IndianPhoneNumber (validated), TokenPair
- `domain/entities/user.py` — User, OAuthAccount dataclasses with `is_locked()` and `requires_mfa()` logic
- `domain/entities/tokens.py` — RefreshToken, EmailVerificationToken, PasswordResetToken with `is_valid()`
- `domain/entities/otp_record.py` — OTPRecord with `is_valid()` and `is_send_cooldown_active()`
- `domain/repositories/i_user_repository.py` — IUserRepository, IOAuthAccountRepository (ABC)
- `domain/repositories/i_token_repository.py` — ITokenRepository (ABC)
- `domain/repositories/i_otp_repository.py` — IOTPRepository (ABC)
- `domain/repositories/i_verification_repository.py` — IEmailVerificationRepository, IPasswordResetRepository (ABC)

## Application Layer (Steps 4–5)
- `application/services/password_hasher.py` — Argon2id hash/verify via passlib
- `application/services/jwt_service.py` — RS256 sign/decode, refresh token creation, MFA-pending token, JWKS endpoint
- `application/services/aes_encryption_service.py` — AES-256-GCM encrypt/decrypt for TOTP secrets
- `application/services/totp_service.py` — pyotp TOTP: generate secret, provisioning URI, verify with ±1 window
- `application/dtos/auth_dtos.py` — all Pydantic v2 request/response schemas (15 models)
- `application/services/auth_application_service.py` — all 12 auth flows: register, verify-email, login, OAuth, OTP send/verify, token refresh, logout, MFA setup/confirm/verify, password change/reset/forgot, profile update

## Infrastructure — Persistence (Step 6)
- `infrastructure/persistence/database.py` — async SQLAlchemy engine + session factory
- `infrastructure/persistence/models.py` — ORM models in `auth` schema: UserModel, OAuthAccountModel, EmailVerificationTokenModel, PasswordResetTokenModel
- `infrastructure/persistence/repositories/sqlalchemy_user_repository.py` — SQLAlchemyUserRepository + SQLAlchemyOAuthAccountRepository
- `infrastructure/persistence/repositories/sqlalchemy_verification_repository.py` — email verification + password reset repositories

## Infrastructure — Cache (Step 6)
- `infrastructure/cache/redis_client.py` — async Redis client factory
- `infrastructure/cache/redis_token_repository.py` — refresh token store with O(1) find via reverse-lookup key, bulk revocation via SCAN+DEL
- `infrastructure/cache/redis_otp_repository.py` — OTP store with attempt counter
- `infrastructure/cache/redis_rate_limiter.py` — Redis sorted set sliding window
- `infrastructure/cache/redis_replay_cache.py` — MFA TOTP replay prevention

## Infrastructure — Adapters (Step 8)
- `infrastructure/adapters/twilio_sms_adapter.py` — Twilio OTP send with tenacity retry
- `infrastructure/adapters/aws_ses_adapter.py` — SES email with HTML templates + tenacity retry
- `infrastructure/adapters/hibp_adapter.py` — k-anonymity HIBP check; fail-open on timeout
- `infrastructure/adapters/google_oauth_adapter.py` — authlib PKCE Google OAuth
- `infrastructure/adapters/facebook_oauth_adapter.py` — authlib Facebook OAuth
- `infrastructure/adapters/aws_secrets_adapter.py` — Secrets Manager loader for startup

## Presentation Layer (Step 10)
- `presentation/middleware/security_headers.py` — HSTS, CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Cache-Control: no-store
- `presentation/middleware/request_logging.py` — UUID request_id, structlog JSON, X-Request-ID header, latency_ms
- `presentation/middleware/global_exception_handler.py` — ValueError→400, PermissionError→403, LookupError→423, Exception→500
- `presentation/dependencies.py` — get_db, get_redis, get_current_user, require_admin
- `presentation/routers/auth_router.py` — 13 auth endpoints
- `presentation/routers/admin_auth_router.py` — MFA setup/confirm/verify
- `presentation/routers/users_router.py` — profile + change-password
- `presentation/routers/jwks_router.py` — /.well-known/jwks.json
- `presentation/routers/health_router.py` — /health with DB+Redis check
- `main.py` — app factory, lifespan (secrets load + wiring), middleware + router registration

## Database Migrations
- `alembic.ini` — alembic configuration
- `alembic/env.py` — async alembic with auto-schema detection
- `alembic/versions/0001_create_auth_schema.py` — creates auth schema + all 4 tables + all indexes

## Tests (Steps 3, 5, 7, 9, 11)
- `tests/domain/test_value_objects.py` — IndianPhoneNumber PBT + parametrize, TokenPair, UserRole
- `tests/domain/test_entities.py` — User lockout, OTPRecord validity, token validity
- `tests/application/test_auth_service_register.py` — registration flows + HIBP + duplicate email
- `tests/application/test_auth_service_login.py` — success, wrong password, 5-failure lockout, locked account, unverified email
- `tests/application/test_auth_service_otp.py` — OTP send/verify, cooldown, attempt limit, expiry
- `tests/application/test_password_hasher.py` — Hypothesis PBT roundtrip + uniqueness
- `tests/infrastructure/test_redis_token_repository.py` — store, find, revoke, bulk revoke (fakeredis)
- `tests/infrastructure/test_redis_rate_limiter.py` — within limit, at limit, key isolation (fakeredis)
- `tests/infrastructure/test_hibp_adapter.py` — breached detected, safe not detected, timeout fail-open
- `tests/integration/test_register_login_flow.py` — full flow skeleton (requires docker-compose DB)
- `tests/conftest.py` — shared fixtures: fake_redis, make_user, mock_hibp, mock_sms, mock_email

## Documentation
- `README.md` — setup, test, migration, API endpoint reference
