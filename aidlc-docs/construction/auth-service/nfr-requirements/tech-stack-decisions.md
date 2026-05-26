# Tech Stack Decisions — Unit 1: Auth Microservice

---

## Runtime & Framework

| Component | Choice | Version | Rationale |
|---|---|---|---|
| Language | Python | 3.11+ | Matches overall backend decision; asyncio support |
| Web framework | FastAPI | 0.111+ | Async, auto OpenAPI docs, Pydantic v2, dependency injection |
| ASGI server | Uvicorn | 0.29+ | Production-grade async server for FastAPI |
| Process manager | None (Docker) | — | Docker manages process lifecycle; Uvicorn runs directly |

---

## Security Libraries

| Component | Library | Version | Rationale |
|---|---|---|---|
| Password hashing | `passlib[argon2]` | 1.7.4+ | Argon2id support with configurable parameters; battle-tested |
| JWT (access tokens) | `python-jose[cryptography]` | 3.3+ | RS256 support; JWK set support for JWKS endpoint |
| AES encryption (TOTP secret) | `cryptography` | 42+ | AES-256-GCM for TOTP secret encryption; industry standard |
| TOTP (MFA) | `pyotp` | 2.9+ | RFC 6238 TOTP; QR code provisioning URI generation |
| OAuth 2.0 (Google + Facebook) | `authlib` | 1.3+ | PKCE support; handles token exchange and profile fetch |
| Input validation | `pydantic` v2 | 2.7+ | Built into FastAPI; strict mode for all request schemas |

---

## Data Storage

| Component | Choice | Config | Rationale |
|---|---|---|---|
| Primary database | PostgreSQL 15 | AWS RDS Multi-AZ | Relational; ACID guarantees for User entity |
| ORM | SQLAlchemy | 2.0+ (async) | Type-safe queries; async support; Alembic integration |
| Migrations | Alembic | 1.13+ | Schema version control; auto-generate from models |
| Cache / token store | Redis | AWS ElastiCache cache.t3.micro | Refresh tokens, OTP, rate limit counters, MFA replay prevention |
| Redis client | `redis[hiredis]` | 5.0+ | Async client; hiredis for parsing performance |

---

## External Service Clients

| Service | Library | Rationale |
|---|---|---|
| AWS SES (email) | `boto3` | Official AWS SDK; async via `aioboto3` wrapper |
| AWS Secrets Manager | `boto3` | Fetch JWT private key, AES key, DB password at startup |
| Twilio SMS | `twilio` | Official SDK; OTP + order SMS |
| HIBP (breached passwords) | `httpx` (async) | k-anonymity SHA-1 prefix API; no dedicated SDK needed |

---

## Testing Stack

| Component | Library | Version | Purpose |
|---|---|---|---|
| Test runner | `pytest` | 8.0+ | Standard Python test runner |
| Async test support | `pytest-asyncio` | 0.23+ | Test async FastAPI endpoints |
| HTTP test client | `httpx` | 0.27+ | Async ASGI test client (replaces TestClient for async) |
| Coverage | `coverage` + `pytest-cov` | — | Line coverage reporting; enforced at 80% in CI |
| Property-based testing | `hypothesis` | 6.100+ | PBT for password validation, TTL logic, phone normalization |
| Mocking | `pytest-mock` + `unittest.mock` | — | Mock external adapters (Twilio, SES, HIBP, OAuth) |
| Test DB | `pytest-postgresql` or Docker Compose PostgreSQL | — | Real PostgreSQL for integration tests (no mocks) |
| Factories | `factory-boy` | 3.3+ | Test data factories for User, Token entities |

---

## Code Quality

| Component | Tool | Config |
|---|---|---|
| Type checking | `mypy` | strict mode (`--strict`) |
| Linting | `ruff` | replaces flake8 + isort + pyupgrade |
| Formatting | `black` | line-length=88 |
| Pre-commit hooks | `pre-commit` | runs ruff + black + mypy on commit |

---

## Observability

| Component | Choice | Rationale |
|---|---|---|
| Logging | Python `structlog` | Structured JSON logs; integrates with CloudWatch |
| Log destination | AWS CloudWatch Logs | Centralized; alarm integration |
| Metrics | AWS CloudWatch Metrics (via boto3) | Login success/failure counts, OTP send counts |
| Tracing | AWS X-Ray (optional, post-MVP) | Distributed tracing across microservices |
| Health check | FastAPI `/health` endpoint | Returns 200 + service status; used by ALB health checks |

---

## Containerization & CI/CD

| Component | Choice |
|---|---|
| Container runtime | Docker |
| Base image | `python:3.11-slim` (pinned digest in production Dockerfile) |
| CI/CD | GitHub Actions |
| Pipeline steps | lint → type-check → test (with coverage gate) → build Docker image → push to ECR → deploy to EC2 |
| Image registry | AWS ECR (Elastic Container Registry) |
| Secrets in CI | GitHub Actions OIDC → AWS IAM role (no long-lived AWS keys in CI) |
