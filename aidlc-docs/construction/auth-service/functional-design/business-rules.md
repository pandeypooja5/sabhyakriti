# Business Rules — Unit 1: Auth Microservice

---

## Password Rules

| ID | Rule |
|---|---|
| BR-AUTH-001 | Password minimum length: 8 characters |
| BR-AUTH-002 | Password must not appear in known breached password lists (checked via Have I Been Pwned k-anonymity API at registration and password reset) |
| BR-AUTH-003 | Passwords stored exclusively as Argon2id hashes — no plaintext, MD5, SHA-1, or bcrypt |
| BR-AUTH-004 | Argon2id parameters: memory=64MB, iterations=3, parallelism=2 (tuned for <500ms on server hardware) |

---

## Account Lockout & Brute-Force Protection

| ID | Rule |
|---|---|
| BR-AUTH-005 | After 5 consecutive failed login attempts for a given email: set `locked_until = NOW() + 15 minutes`; return HTTP 423 with retry-after header |
| BR-AUTH-006 | On successful login: reset `failed_login_attempts = 0` and clear `locked_until` |
| BR-AUTH-007 | Lockout is per-account (email), not per-IP — prevents distributed attacks from locking out innocent users via IP-based blocks |
| BR-AUTH-008 | Rate limiting (additional layer, enforced by middleware): max 10 login requests per minute per IP; max 5 registration requests per minute per IP |
| BR-AUTH-009 | Admin login additionally enforces: max 3 failed attempts per 10 minutes before temporary IP block (more strict than customer accounts) |

---

## Email Verification

| ID | Rule |
|---|---|
| BR-AUTH-010 | Email verification is **mandatory** — users with `is_email_verified = FALSE` receive HTTP 403 on login with message: "Please verify your email before logging in." |
| BR-AUTH-011 | Verification token TTL = 48 hours; after expiry user must request a new verification email |
| BR-AUTH-012 | Verification token is single-use: `used_at` is set on first successful verification; replay attempts return HTTP 400 |
| BR-AUTH-013 | Resend verification email: max 3 resend requests per hour per email address |
| BR-AUTH-014 | OAuth registrations (Google, Facebook) are treated as email-verified (`is_email_verified = TRUE`) since OAuth providers have already verified the email |

---

## OAuth & Account Linking

| ID | Rule |
|---|---|
| BR-AUTH-015 | If OAuth email matches an existing User: **auto-link** — add OAuthAccount record to existing user and log them in; no separate prompt |
| BR-AUTH-016 | If OAuth email does not exist: create new User (`is_email_verified = TRUE`, `hashed_password = NULL`) and link OAuthAccount |
| BR-AUTH-017 | A user can have at most one OAuthAccount per provider (e.g., cannot link two Google accounts) |
| BR-AUTH-018 | Duplicate link attempt (same provider + user) is idempotent — update `provider_email` if changed, return success |
| BR-AUTH-019 | OAuth `state` parameter validated on callback to prevent CSRF — state is a random token stored in a short-lived Redis key tied to the session |
| BR-AUTH-020 | PKCE (Proof Key for Code Exchange) used for Google and Facebook OAuth flows |

---

## Phone OTP Rules

| ID | Rule |
|---|---|
| BR-AUTH-021 | Phone number format: exactly 10 digits, first digit must be 6, 7, 8, or 9 (Indian mobile numbers) |
| BR-AUTH-022 | OTP is 6 digits, cryptographically random (secrets.randbelow), stored as Argon2id hash |
| BR-AUTH-023 | OTP TTL = 10 minutes from creation |
| BR-AUTH-024 | Max 3 verification attempts per OTP — on 3rd failure: OTP is invalidated (`expires_at = NOW()`); user must request new OTP |
| BR-AUTH-025 | Resend cooldown: 1 minute must pass between consecutive OTP send requests for the same phone number (checked via `last_sent_at`) |
| BR-AUTH-026 | Max 5 OTP send requests per phone number per hour (prevents SMS cost abuse) |
| BR-AUTH-027 | Successful OTP verification sets `is_phone_verified = TRUE` on the User; creates User if first-time phone login |

---

## JWT Token Rules

| ID | Rule |
|---|---|
| BR-AUTH-028 | Access token algorithm: RS256 (asymmetric); private key signs, public key shared with all microservices for independent validation |
| BR-AUTH-029 | Access token TTL = 30 minutes; claims: `sub` (user_id), `role`, `email`, `iat`, `exp`, `jti` |
| BR-AUTH-030 | Refresh token TTL = 30 days; stored as SHA-256 hash in Redis with key pattern `refresh:{user_id}:{token_id}` |
| BR-AUTH-031 | Refresh token rotation: issuing a new access token also issues a new refresh token; old refresh token is revoked immediately |
| BR-AUTH-032 | On logout (single device): revoke the specific refresh token from Redis |
| BR-AUTH-033 | On password change: revoke ALL refresh tokens for the user (`DEL refresh:{user_id}:*` pattern) |
| BR-AUTH-034 | MFA-pending token: admin accounts after password verification receive a short-lived (5 min) MFA-pending JWT; full JWT only issued after TOTP verification |

---

## Session & Password Reset Rules

| ID | Rule |
|---|---|
| BR-AUTH-035 | Password change: invalidate ALL existing refresh tokens for that user across all devices |
| BR-AUTH-036 | Password reset link TTL = 2 hours; single-use token (`used_at` set on consumption) |
| BR-AUTH-037 | Password reset links are delivered via email only; no SMS reset path |
| BR-AUTH-038 | Requesting a second password reset while a valid token exists: issue new token, invalidate previous one |
| BR-AUTH-039 | Session cookies (if used instead of localStorage): `Secure`, `HttpOnly`, `SameSite=Strict` attributes mandatory |

---

## Admin MFA Rules

| ID | Rule |
|---|---|
| BR-AUTH-040 | Admin accounts **must** complete MFA setup before accessing any `/api/v1/admin/*` endpoints |
| BR-AUTH-041 | MFA method: TOTP (RFC 6238) via authenticator app (Google Authenticator, Authy, etc.) |
| BR-AUTH-042 | TOTP secret stored AES-256 encrypted in `User.mfa_secret_encrypted`; encryption key from AWS Secrets Manager |
| BR-AUTH-043 | MFA setup: generate TOTP secret → return provisioning URI + QR code → user scans → user submits first TOTP code to confirm → set `mfa_enabled = TRUE` |
| BR-AUTH-044 | Admin login flow: password verify → issue MFA-pending token (5 min TTL) → TOTP verify → issue full JWT |
| BR-AUTH-045 | TOTP window tolerance: accept current 30-second window ± 1 window (covers clock drift) |
| BR-AUTH-046 | Each TOTP code is single-use within its window (replay prevention via Redis `mfa_used:{user_id}:{totp_code}` key with 90s TTL) |

---

## Input Validation Rules

| ID | Rule | Applies To |
|---|---|---|
| BR-AUTH-047 | Email: max 255 chars, RFC 5322 format, lowercase-normalized before storage | Register, login |
| BR-AUTH-048 | Password: 8–128 chars; reject control characters | Register, reset |
| BR-AUTH-049 | Full name: 1–100 chars; strip leading/trailing whitespace | Register, profile update |
| BR-AUTH-050 | Phone number: exactly 10 digits after stripping spaces/dashes; reject non-numeric | OTP send |
| BR-AUTH-051 | All string inputs: reject null bytes; max request body size enforced at 64KB | All endpoints |
