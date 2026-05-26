# Functional Design Plan — Unit 1: Auth Microservice
# Sabhyakriti — Saree eCommerce Website

---

## Execution Checklist

- [x] Step 1: Answer business logic questions (user fills [Answer]: tags below)
- [x] Step 2: Analyze answers — NO ambiguities detected
- [x] Step 3: Generate domain-entities.md
- [x] Step 4: Generate business-rules.md
- [x] Step 5: Generate business-logic-model.md
- [x] Step 6: Present for approval

---

## Context Summary

Unit 1 owns: User, RefreshToken, OTPRecord, PasswordResetToken entities.
Handles: email/password auth, Google OAuth, Facebook OAuth, phone OTP, JWT tokens, password reset, email verification, user profile, admin MFA.
Security rules applied: SECURITY-08 (access control), SECURITY-12 (auth + credential management), SECURITY-11 (rate limiting).

---

## Business Logic Questions

Please fill in the letter choice after each `[Answer]:` tag and let me know when done.

---

## Question 1
After how many consecutive failed login attempts should brute-force protection trigger?

A) 5 failed attempts → account locked for 15 minutes, then auto-unlocks
B) 5 failed attempts → progressive delay (2s, 4s, 8s…) with CAPTCHA after 3 attempts (no hard lockout)
C) 3 failed attempts → account locked until user resets password via email
D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 2
Must users verify their email address before they can log in?

A) Yes — email verification required before first login; unverified accounts cannot log in
B) No — users can log in immediately; verification is optional (just a nudge)
C) Soft enforcement — users can log in but get a persistent banner until verified; checkout is blocked without verification
D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 3
If a user tries to register with an email that already exists via a social login (Google/Facebook), what should happen?

A) Auto-link accounts — if the OAuth email matches an existing account, log them in and link the OAuth provider to that account
B) Block registration — show an error: "An account with this email already exists. Please log in."
C) Prompt the user to link — ask: "An account exists with this email. Link your Google account to it?"
D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 4
When a user changes their password, what happens to their other active sessions?

A) Invalidate all existing sessions (all devices logged out); user must log in again everywhere
B) Keep all existing sessions active (only apply new password to future logins)
C) Invalidate all sessions except the current one (user stays logged in on the device they changed the password from)
D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 5
What are the expiry rules for the following tokens?

A) Short-lived: access token 15 min, refresh token 7 days, OTP 5 min, email verification 24 hrs, password reset 1 hr
B) Medium-lived: access token 30 min, refresh token 30 days, OTP 10 min, email verification 48 hrs, password reset 2 hrs
C) Other (please describe after [Answer]: tag below)

[Answer]: B
