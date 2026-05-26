# Business Logic Model — Unit 1: Auth Microservice

---

## Flow 1: Email/Password Registration

```
Input: email, password, full_name

1. Validate email format (BR-AUTH-047) → 400 if invalid
2. Validate password length and complexity (BR-AUTH-001, BR-AUTH-002)
   └─ Check HIBP k-anonymity API for breached password → 400 if found
3. Normalise email to lowercase
4. Check User.email uniqueness → 409 Conflict if duplicate
5. Hash password with Argon2id (BR-AUTH-003, BR-AUTH-004)
6. Create User { is_email_verified=FALSE, role=CUSTOMER }
7. Generate random URL-safe token (32 bytes) → hash with SHA-256 → create EmailVerificationToken (TTL 48h)
8. Dispatch email: verification link = https://sabhyakriti.com/verify-email?token=<raw_token>
9. Return 201 { message: "Registration successful. Please verify your email." }
   └─ Do NOT issue JWT at this stage
```

---

## Flow 2: Email Verification

```
Input: token (from URL query param)

1. SHA-256 hash the input token
2. Lookup EmailVerificationToken by token_hash → 400 "Invalid or expired link" if not found
3. Check expires_at > NOW() → 400 "Link expired. Request a new one." if stale
4. Check used_at IS NULL → 400 "Link already used." if replayed
5. Set User.is_email_verified = TRUE
6. Set EmailVerificationToken.used_at = NOW()
7. Issue TokenPair (access + refresh tokens)
8. Return 200 { tokens, user_profile }
```

---

## Flow 3: Email/Password Login

```
Input: email, password

1. Check rate limit (10 req/min per IP) → 429 if exceeded
2. Normalise email to lowercase
3. Lookup User by email → 401 "Invalid credentials" if not found (no email enumeration)
4. Check User.is_active = TRUE → 403 "Account suspended" if not
5. Check User.locked_until:
   └─ If locked_until > NOW() → 423 { retry_after: seconds_remaining }
6. Check User.is_email_verified = TRUE → 403 "Please verify your email" if not
7. Verify password with Argon2id:
   └─ On FAILURE:
       a. Increment User.failed_login_attempts
       b. If failed_login_attempts >= 5: set locked_until = NOW() + 15 min
       c. Return 401 "Invalid credentials"
   └─ On SUCCESS:
       a. Reset User.failed_login_attempts = 0, locked_until = NULL
8. If User.role = ADMIN and User.mfa_enabled = TRUE:
   └─ Issue MFA-pending JWT (5 min TTL, scope=mfa_pending) → return 200 { mfa_required: true, mfa_token }
   └─ (Full JWT issued only after MFA verification — see Flow 8)
9. Issue TokenPair (access 30min + refresh 30 days)
10. Return 200 { tokens, user_profile }
```

---

## Flow 4: Google OAuth Login / Registration

```
Input: code, redirect_uri (from frontend OAuth callback)

1. Validate OAuth state parameter against Redis stored state → 400 if mismatch (CSRF guard, BR-AUTH-019)
2. Exchange code for Google tokens via GoogleOAuthAdapter
3. Fetch Google user profile: { sub, email, name, picture }
4. Lookup OAuthAccount by (provider=GOOGLE, provider_user_id=sub):
   └─ FOUND: load linked User → go to step 7
   └─ NOT FOUND: continue to step 5
5. Lookup User by email:
   └─ FOUND (existing account): auto-link → create OAuthAccount { user_id, GOOGLE, sub } (BR-AUTH-015)
   └─ NOT FOUND: create new User { is_email_verified=TRUE, hashed_password=NULL } + OAuthAccount (BR-AUTH-016)
6. Reload User
7. Check User.is_active = TRUE → 403 if suspended
8. Issue TokenPair
9. Return 200 { tokens, user_profile, is_new_user: bool }
```

---

## Flow 5: Phone OTP — Send

```
Input: phone_number

1. Validate phone format (BR-AUTH-021) → 400 if invalid
2. Check rate limit: max 5 OTP requests/hour per phone (BR-AUTH-026) → 429 if exceeded
3. Check OTPRecord for phone:
   └─ If exists and last_sent_at > NOW() - 1 min → 429 "Please wait before requesting a new OTP" (BR-AUTH-025)
4. Generate 6-digit OTP with secrets.randbelow(1_000_000), zero-padded
5. Hash OTP with Argon2id → upsert OTPRecord { phone, otp_hash, attempt_count=0, last_sent_at=NOW(), expires_at=NOW()+10min }
6. Dispatch SMS via TwilioSMSAdapter
7. Return 200 { message: "OTP sent", expires_in: 600 }
   └─ Never return OTP value in response
```

---

## Flow 6: Phone OTP — Verify

```
Input: phone_number, otp_code

1. Validate phone format → 400 if invalid
2. Lookup OTPRecord by phone_number → 400 "No OTP found" if missing
3. Check expires_at > NOW() → 400 "OTP expired" if stale
4. Check used_at IS NULL → 400 "OTP already used" if replayed
5. Check attempt_count < 3 → 400 "OTP invalidated. Request a new one." if exceeded (BR-AUTH-024)
6. Verify OTP with Argon2id:
   └─ On FAILURE: increment attempt_count → if now >= 3: set expires_at = NOW() → 400 "Invalid OTP"
   └─ On SUCCESS:
       a. Set OTPRecord.used_at = NOW()
       b. Lookup User by phone_number:
          └─ NOT FOUND: create new User { is_phone_verified=TRUE, is_email_verified=FALSE }
          └─ FOUND: set is_phone_verified = TRUE
       c. Issue TokenPair
       d. Return 200 { tokens, user_profile, is_new_user: bool }
```

---

## Flow 7: Token Refresh

```
Input: refresh_token (Bearer or cookie)

1. Decode refresh token to extract jti (token_id) and user_id (no signature verification yet)
2. Lookup token_hash = SHA-256(refresh_token) in Redis key refresh:{user_id}:{jti}
   └─ Not found or expired → 401 "Invalid or expired refresh token"
3. Check token is not revoked (revoked_at IS NULL in Redis metadata)
4. Verify RS256 signature → 401 if invalid
5. Check exp claim → 401 if expired
6. Issue new access token (30 min) + new refresh token (30 days) (token rotation)
7. Revoke old refresh token in Redis
8. Return 200 { tokens }
```

---

## Flow 8: Admin MFA Verification (2nd factor)

```
Input: mfa_token (MFA-pending JWT), totp_code

1. Validate mfa_token:
   └─ Verify RS256 signature → 401 if invalid
   └─ Check scope = "mfa_pending" → 403 if wrong scope
   └─ Check exp → 401 if expired (5 min window)
2. Load User by sub (user_id) from token claims
3. Check User.mfa_enabled = TRUE and mfa_secret_encrypted is not null
4. Decrypt mfa_secret_encrypted using AES-256 key from AWS Secrets Manager
5. Validate TOTP code (±1 window tolerance, BR-AUTH-045)
6. Check Redis key mfa_used:{user_id}:{totp_code} → 400 "Code already used" if exists (BR-AUTH-046)
7. On success:
   a. Set Redis key mfa_used:{user_id}:{totp_code} with 90s TTL
   b. Issue full TokenPair (access 30min + refresh 30 days)
8. Return 200 { tokens, user_profile }
```

---

## Flow 9: Password Change

```
Input: current_password, new_password (authenticated request)

1. Verify current_password against User.hashed_password → 401 if wrong
2. Validate new_password (BR-AUTH-001, BR-AUTH-002, BR-AUTH-048)
3. Ensure new_password != current_password → 400 "New password must differ"
4. Hash new_password with Argon2id
5. Update User.hashed_password
6. Revoke ALL refresh tokens for user (Redis: DEL refresh:{user_id}:* pattern) (BR-AUTH-035)
7. Return 200 { message: "Password changed. Please log in again." }
```

---

## Flow 10: Password Reset Request

```
Input: email

1. Normalise email
2. Lookup User by email → return 200 regardless (no email enumeration)
3. If User found and is_active:
   a. Invalidate any existing valid PasswordResetToken for this user
   b. Generate random 32-byte URL-safe token → SHA-256 hash → create PasswordResetToken (TTL 2h)
   c. Dispatch email: reset link = https://sabhyakriti.com/reset-password?token=<raw_token>
4. Return 200 { message: "If that email is registered, you will receive a reset link." }
```

---

## Flow 11: Password Reset Confirmation

```
Input: token, new_password

1. SHA-256 hash the input token
2. Lookup PasswordResetToken by token_hash → 400 if not found
3. Check expires_at > NOW() → 400 "Link expired"
4. Check used_at IS NULL → 400 "Link already used"
5. Validate new_password (BR-AUTH-001, BR-AUTH-002, BR-AUTH-048)
6. Hash new_password with Argon2id
7. Update User.hashed_password; reset failed_login_attempts=0, locked_until=NULL
8. Set PasswordResetToken.used_at = NOW()
9. Revoke ALL refresh tokens for user (BR-AUTH-035)
10. Return 200 { message: "Password reset successful. Please log in." }
```

---

## Flow 12: Logout

```
Input: refresh_token (to identify session)

Single device: SHA-256 hash refresh_token → delete Redis key refresh:{user_id}:{jti} → 200 OK
All devices: delete all Redis keys matching refresh:{user_id}:* → 200 OK
```

---

## Error Response Standards

| Scenario | HTTP Status | Message (never expose internals) |
|---|---|---|
| Invalid credentials | 401 | "Invalid email or password" |
| Account locked | 423 | "Account temporarily locked. Try again in X minutes." |
| Email not verified | 403 | "Please verify your email before logging in." |
| Account suspended | 403 | "Account suspended. Contact support." |
| OTP expired | 400 | "OTP has expired. Please request a new one." |
| Invalid/expired token | 401 | "Invalid or expired token." |
| Rate limit exceeded | 429 | "Too many requests. Please try again later." |
| Duplicate email | 409 | "An account with this email already exists." |
