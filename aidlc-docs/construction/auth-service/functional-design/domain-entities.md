# Domain Entities — Unit 1: Auth Microservice

---

## Entity: User

**Purpose**: Core identity record for every registered user (customer or admin).

| Field | Type | Constraints | Description |
|---|---|---|---|
| `user_id` | UUID | PK, not null | Auto-generated primary key |
| `email` | VARCHAR(255) | UNIQUE, nullable | Email address; null for phone-only OAuth accounts |
| `phone_number` | VARCHAR(15) | UNIQUE, nullable | Indian mobile: 10 digits starting 6-9; null for email-only accounts |
| `hashed_password` | VARCHAR(255) | nullable | Argon2id hash; null for OAuth-only accounts |
| `full_name` | VARCHAR(100) | not null | Display name |
| `profile_picture_url` | VARCHAR(500) | nullable | S3/CloudFront URL |
| `role` | ENUM(CUSTOMER, ADMIN) | not null, default CUSTOMER | Authorization role |
| `is_email_verified` | BOOLEAN | not null, default FALSE | Must be TRUE before customer can log in |
| `is_phone_verified` | BOOLEAN | not null, default FALSE | Set TRUE after first successful OTP verification |
| `is_active` | BOOLEAN | not null, default TRUE | FALSE = soft-deleted or admin-suspended account |
| `failed_login_attempts` | SMALLINT | not null, default 0 | Reset to 0 on successful login |
| `locked_until` | TIMESTAMPTZ | nullable | Non-null when account is temporarily locked |
| `mfa_secret_encrypted` | VARCHAR(255) | nullable | AES-256 encrypted TOTP secret; non-null only for admin accounts with MFA enabled |
| `mfa_enabled` | BOOLEAN | not null, default FALSE | TRUE only for admin accounts after MFA setup confirmed |
| `created_at` | TIMESTAMPTZ | not null, default NOW() | Account creation timestamp |
| `updated_at` | TIMESTAMPTZ | not null, default NOW() | Last update timestamp (auto-updated) |

**Indexes**: `email` (unique), `phone_number` (unique), `role` (for admin queries)

---

## Entity: OAuthAccount

**Purpose**: Links a User to one or more external OAuth providers. Enables auto-linking when same email registers via multiple providers.

| Field | Type | Constraints | Description |
|---|---|---|---|
| `oauth_id` | UUID | PK | Auto-generated |
| `user_id` | UUID | FK → User, not null | Owner user |
| `provider` | ENUM(GOOGLE, FACEBOOK) | not null | OAuth provider |
| `provider_user_id` | VARCHAR(255) | not null | Stable ID from the provider (e.g., Google sub claim) |
| `provider_email` | VARCHAR(255) | nullable | Email from provider at time of link |
| `created_at` | TIMESTAMPTZ | not null, default NOW() | When this provider was linked |

**Indexes**: `(provider, provider_user_id)` unique composite — prevents duplicate provider links

---

## Entity: RefreshToken

**Purpose**: Tracks issued refresh tokens for server-side revocation. Stored in Redis (primary) with DB fallback for audit.

| Field | Type | Constraints | Description |
|---|---|---|---|
| `token_id` | UUID | PK | Matches the `jti` claim in the refresh JWT |
| `user_id` | UUID | FK → User, not null | Token owner |
| `token_hash` | VARCHAR(64) | not null, UNIQUE | SHA-256 hash of the raw refresh token string |
| `device_hint` | VARCHAR(100) | nullable | User-agent or device label for display in "active sessions" |
| `expires_at` | TIMESTAMPTZ | not null | TTL = 30 days from issuance |
| `revoked_at` | TIMESTAMPTZ | nullable | Set when token is explicitly revoked (logout/password-change) |
| `created_at` | TIMESTAMPTZ | not null, default NOW() | |

**Indexes**: `user_id` (for bulk revocation on password change), `token_hash` (lookup on refresh)

---

## Entity: OTPRecord

**Purpose**: Stores a single pending OTP per phone number. Replaced on each new OTP request.

| Field | Type | Constraints | Description |
|---|---|---|---|
| `otp_id` | UUID | PK | |
| `phone_number` | VARCHAR(15) | not null, UNIQUE | One pending OTP per phone at a time |
| `otp_hash` | VARCHAR(255) | not null | Argon2id hash of the 6-digit OTP |
| `attempt_count` | SMALLINT | not null, default 0 | Incremented on each failed verify; max 3 before OTP invalidated |
| `last_sent_at` | TIMESTAMPTZ | not null | Used to enforce 1-minute resend cooldown |
| `expires_at` | TIMESTAMPTZ | not null | TTL = 10 minutes from creation |
| `used_at` | TIMESTAMPTZ | nullable | Set when OTP is successfully verified; prevents replay |

**Indexes**: `phone_number` (unique — fast lookup for verification)

---

## Entity: EmailVerificationToken

**Purpose**: One-time token sent to user's email to confirm ownership before first login.

| Field | Type | Constraints | Description |
|---|---|---|---|
| `token_id` | UUID | PK | |
| `user_id` | UUID | FK → User, not null | Target user |
| `token_hash` | VARCHAR(64) | not null, UNIQUE | SHA-256 hash of the random URL-safe token |
| `expires_at` | TIMESTAMPTZ | not null | TTL = 48 hours from creation |
| `used_at` | TIMESTAMPTZ | nullable | Set when verified; prevents replay |

---

## Entity: PasswordResetToken

**Purpose**: Single-use time-limited token for password reset via email link.

| Field | Type | Constraints | Description |
|---|---|---|---|
| `token_id` | UUID | PK | |
| `user_id` | UUID | FK → User, not null | |
| `token_hash` | VARCHAR(64) | not null, UNIQUE | SHA-256 hash of the random URL-safe token |
| `expires_at` | TIMESTAMPTZ | not null | TTL = 2 hours from creation |
| `used_at` | TIMESTAMPTZ | nullable | Set when reset completes; prevents replay |

---

## Value Objects

| Value Object | Type | Values / Rules |
|---|---|---|
| `UserRole` | Enum | CUSTOMER, ADMIN |
| `OAuthProvider` | Enum | GOOGLE, FACEBOOK |
| `TokenPair` | VO | `{ access_token: str, refresh_token: str, token_type: "Bearer", expires_in: 1800 }` |
| `IndianPhoneNumber` | VO | 10 digits, starts with 6–9, no country code stored (implied +91) |

---

## Entity Relationships

```
User (1) ──────── (N) OAuthAccount       user can have multiple OAuth providers
User (1) ──────── (N) RefreshToken       user can have many active sessions
User (1) ──────── (0..1) OTPRecord       at most one pending OTP per user (by phone)
User (1) ──────── (0..N) EmailVerificationToken
User (1) ──────── (0..N) PasswordResetToken
```
