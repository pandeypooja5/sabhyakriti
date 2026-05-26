# sabhyakriti-auth-service

Auth Microservice for Sabhyakriti — Saree eCommerce Platform.

Handles: email/password auth, Google OAuth, Facebook OAuth, Phone OTP, JWT sessions, Admin MFA.

## Local Setup

```bash
cp .env.example .env          # fill in values
docker-compose -f docker-compose.dev.yml up
```

Service runs at http://localhost:8001. Docs at http://localhost:8001/docs.

## Run Tests

```bash
pip install -r requirements-dev.txt
pytest                         # runs all tests with 80% coverage gate
pytest tests/domain/           # domain-only
pytest tests/application/      # application-only (no DB/Redis required)
pytest -m "not integration"    # skip integration tests
```

## DB Migrations

```bash
alembic upgrade head           # apply all migrations
alembic revision --autogenerate -m "description"   # generate new migration
```

## Environment Variables

See `.env.example` for all required variables. In production, sensitive values are loaded from AWS Secrets Manager at startup.

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/v1/auth/register | — | Register with email + password |
| POST | /api/v1/auth/login | — | Login (email/password) |
| GET  | /api/v1/auth/oauth/{provider}/init | — | Start OAuth flow |
| GET  | /api/v1/auth/oauth/{provider}/callback | — | OAuth callback |
| POST | /api/v1/auth/verify-email | — | Verify email token |
| POST | /api/v1/auth/otp/send | — | Send phone OTP |
| POST | /api/v1/auth/otp/verify | — | Verify phone OTP |
| POST | /api/v1/auth/refresh | — | Refresh access token |
| POST | /api/v1/auth/logout | JWT | Logout current session |
| POST | /api/v1/auth/logout-all | JWT | Logout all sessions |
| POST | /api/v1/auth/forgot-password | — | Request password reset |
| POST | /api/v1/auth/reset-password | — | Reset password |
| POST | /api/v1/auth/admin/mfa/setup | JWT+Admin | Setup TOTP MFA |
| POST | /api/v1/auth/admin/mfa/confirm-setup | JWT+Admin | Confirm MFA setup |
| POST | /api/v1/auth/admin/mfa/verify | MFA token | Verify TOTP |
| GET  | /api/v1/users/me | JWT | Get profile |
| PATCH | /api/v1/users/me | JWT | Update profile |
| POST | /api/v1/users/me/change-password | JWT | Change password |
| GET  | /auth/.well-known/jwks.json | — | RS256 public key |
| GET  | /health | — | Health check |
