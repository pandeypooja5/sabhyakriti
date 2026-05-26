# NFR Requirements Plan — Unit 1: Auth Microservice
# Sabhyakriti — Saree eCommerce Website

---

## Execution Checklist

- [x] Step 1: Answer NFR questions (user fills [Answer]: tags below)
- [x] Step 2: Analyze answers — NO ambiguities detected
- [x] Step 3: Generate nfr-requirements.md
- [x] Step 4: Generate tech-stack-decisions.md
- [x] Step 5: Present for approval — user pre-approved with "Continue to Next Stage"

---

## Already Decided (from requirements.md + design)

The following NFRs are already locked in — no questions needed:

| NFR | Decision |
|---|---|
| API response time | < 500ms (NFR-PERF-04) |
| Uptime target | 99.9% (NFR-SCAL-04) |
| Password hashing | Argon2id (SECURITY-12) |
| JWT algorithm | RS256 (BR-AUTH-028) |
| Rate limiting | Redis sliding window (BR-AUTH-008) |
| Security rules | SECURITY-01 through SECURITY-15 fully enforced |
| Runtime | Python 3.11 + FastAPI |
| Database | PostgreSQL 15 on AWS RDS |
| Deployment | Docker on AWS EC2 |
| Secrets management | AWS Secrets Manager |

---

## NFR Questions

Please fill in the letter choice after each `[Answer]:` tag and let me know when done.

---

## Question 1
What is the expected peak concurrent user load at launch for the Auth Service?
(This determines EC2 instance type and Redis sizing.)

A) Small launch — up to 500 concurrent users; t3.medium EC2 + single Redis node is sufficient
B) Medium launch — up to 2,000 concurrent users; t3.large EC2 + ElastiCache Redis with 1 read replica
C) Large launch — up to 10,000+ concurrent users; c5.xlarge EC2 with Auto Scaling + Redis Cluster
D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 2
For the Redis token store (refresh tokens + OTP + rate limiting) — what availability level is acceptable?

A) Single Redis node (ElastiCache) — simpler, lower cost; acceptable if a short Redis outage causes users to need to re-login (MVP approach)
B) Redis with 1 standby replica (ElastiCache Multi-AZ) — automatic failover in ~60s; no data loss on primary failure
C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 3
What is the required test coverage minimum for the Auth Microservice?

A) 80% line coverage — industry standard; sufficient for production
B) 90% line coverage — higher confidence for security-critical auth code
C) No minimum enforced — write tests for all critical paths but don't enforce a coverage threshold
D) Other (please describe after [Answer]: tag below)

[Answer]: A
