# Infrastructure Design — Unit 1: Auth Microservice

---

## AWS Service Mapping

| Logical Component | AWS Service | SKU / Config | Notes |
|---|---|---|---|
| Application compute | EC2 | t3.medium (2 vCPU, 4 GB) | Private subnet; Docker container; 1 instance MVP |
| Load balancer | Application Load Balancer | Shared ALB (Unit 8) | Path-based routing → target group port 8001 |
| Database | RDS PostgreSQL 15 | db.t3.micro, Multi-AZ, 20 GB gp3 | `auth` schema; encrypted at rest; enforce_ssl=on |
| Token / session cache | ElastiCache Redis 7 | cache.t3.micro, single node | Refresh tokens, OTP, rate limiting, CSRF state |
| Secrets | AWS Secrets Manager | 3 secrets | JWT private key, AES key, DB password |
| Email | AWS SES | `no-reply@sabhyakriti.com` | DKIM + SPF configured; sandbox → production approval needed |
| Logs | CloudWatch Logs | Log group: `/sabhyakriti/auth-service` | Retention: 90 days; encrypted with AWS-managed key |
| Metrics & alarms | CloudWatch | Custom namespace `Sabhyakriti/Auth` | Login failures > 50/min → SNS alert |
| Container registry | ECR | `sabhyakriti/auth-service` | Image scanning on push; pinned digest in task def |
| CI/CD | GitHub Actions + ECR + EC2 SSM | — | OIDC → IAM role; SSM Run Command for deploy |

---

## Network Architecture

```
Internet
    |
    v
[ALB — public subnet, port 443 HTTPS]
    |  (path: /api/v1/auth/*, /auth/.well-known/*, /health)
    v
[EC2 t3.medium — private subnet 10.0.1.x, port 8001]
    |              |
    v              v
[RDS Multi-AZ    [ElastiCache Redis
 10.0.2.x:5432]   10.0.3.x:6379]
```

**Security groups**:
- `sg-alb`: inbound 443 from 0.0.0.0/0; outbound 8001 to `sg-auth-ec2`
- `sg-auth-ec2`: inbound 8001 from `sg-alb` only; outbound 5432 to `sg-rds`, 6379 to `sg-redis`, 443 to 0.0.0.0/0 (for external APIs: HIBP, Twilio, Google, Facebook)
- `sg-rds`: inbound 5432 from `sg-auth-ec2` only
- `sg-redis`: inbound 6379 from `sg-auth-ec2` only

---

## Deployment Architecture

```
GitHub PR merged to main
    |
    v
GitHub Actions workflow (auth-service.yml)
    1. checkout + setup Python 3.11
    2. ruff lint + mypy type-check
    3. pytest --cov (fail if coverage < 80%)
    4. docker build --platform linux/amd64 -t auth-service .
    5. docker tag → ECR push (with commit SHA tag + latest)
    6. AWS SSM Run Command → EC2:
       docker pull <ecr-image>
       docker stop auth-service || true
       docker run -d --name auth-service \
         --env-file /etc/sabhyakriti/auth.env \
         -p 8001:8001 \
         --restart unless-stopped \
         <ecr-image>
    7. ALB health check passes → deployment complete
```

**Environment variables** (loaded from `/etc/sabhyakriti/auth.env` on EC2; values injected by CDK at provisioning from Secrets Manager):
```
DATABASE_URL=postgresql+asyncpg://...@rds-endpoint/sabhyakriti_auth
REDIS_URL=redis://elasticache-endpoint:6379/0
AWS_REGION=ap-south-1
SECRETS_MANAGER_JWT_KEY=sabhyakriti/auth/jwt-private-key
SECRETS_MANAGER_AES_KEY=sabhyakriti/auth/aes-key
FRONTEND_ORIGIN=https://sabhyakriti.com
GOOGLE_CLIENT_ID=<from-secrets-manager>
FACEBOOK_CLIENT_ID=<from-secrets-manager>
TWILIO_ACCOUNT_SID=<from-secrets-manager>
LOG_LEVEL=INFO
```

---

## Database Schema (auth)

All tables reside in the `auth` PostgreSQL schema, owned by `auth_service_user` DB role.

```sql
-- auth_service_user has CONNECT + USAGE on auth schema + CRUD on all auth tables
-- No cross-schema reads from this role

CREATE SCHEMA IF NOT EXISTS auth;

CREATE TABLE auth.users (
    user_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE,
    phone_number    VARCHAR(15) UNIQUE,
    hashed_password VARCHAR(255),
    full_name       VARCHAR(100) NOT NULL,
    profile_picture_url VARCHAR(500),
    role            VARCHAR(20) NOT NULL DEFAULT 'CUSTOMER',
    is_email_verified   BOOLEAN NOT NULL DEFAULT FALSE,
    is_phone_verified   BOOLEAN NOT NULL DEFAULT FALSE,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    failed_login_attempts SMALLINT NOT NULL DEFAULT 0,
    locked_until    TIMESTAMPTZ,
    mfa_secret_encrypted VARCHAR(255),
    mfa_enabled     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE auth.oauth_accounts (
    oauth_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES auth.users(user_id) ON DELETE CASCADE,
    provider            VARCHAR(20) NOT NULL,
    provider_user_id    VARCHAR(255) NOT NULL,
    provider_email      VARCHAR(255),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (provider, provider_user_id)
);

CREATE TABLE auth.email_verification_tokens (
    token_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES auth.users(user_id) ON DELETE CASCADE,
    token_hash  VARCHAR(64) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE auth.password_reset_tokens (
    token_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES auth.users(user_id) ON DELETE CASCADE,
    token_hash  VARCHAR(64) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- OTP stored in Redis only (no DB table needed — Redis handles TTL natively)
-- Refresh tokens stored in Redis only
```

**Indexes** (in addition to PK and UNIQUE constraints):
```sql
CREATE INDEX idx_users_email ON auth.users(email);
CREATE INDEX idx_users_phone ON auth.users(phone_number);
CREATE INDEX idx_users_role ON auth.users(role);
CREATE INDEX idx_oauth_user_id ON auth.oauth_accounts(user_id);
CREATE INDEX idx_evt_user_id ON auth.email_verification_tokens(user_id);
CREATE INDEX idx_prt_user_id ON auth.password_reset_tokens(user_id);
```

---

## Redis Key Design

| Key Pattern | TTL | Purpose |
|---|---|---|
| `refresh:{user_id}:{jti}` | 30 days | Refresh token hash + revoked flag |
| `otp:{phone_number}` | 10 minutes | OTP hash + attempt count + last_sent_at |
| `ratelimit:login:{ip}` | 60 seconds (sliding) | Login rate limit counter |
| `ratelimit:register:{ip}` | 60 seconds (sliding) | Registration rate limit counter |
| `ratelimit:otp_send:{phone}` | 1 hour | OTP send abuse prevention |
| `oauth_state:{state}` | 10 minutes | CSRF state for OAuth flows |
| `mfa_used:{user_id}:{totp_code}` | 90 seconds | TOTP replay prevention |

---

## CloudWatch Alarms

| Alarm | Metric | Threshold | Action |
|---|---|---|---|
| High login failure rate | `Sabhyakriti/Auth LoginFailure` | > 50 failures/min | SNS → admin email alert |
| Auth service 5xx errors | ALB `HTTPCode_Target_5XX_Count` | > 10 in 5 min | SNS alert |
| EC2 CPU high | `CPUUtilization` | > 80% for 10 min | SNS alert (manual scale-up for MVP) |
| Redis memory | `DatabaseMemoryUsagePercentage` | > 80% | SNS alert |
| OTP send spike | `Sabhyakriti/Auth OTPSent` | > 100 in 5 min | SNS alert (possible abuse) |
