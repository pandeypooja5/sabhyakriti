# NFR Requirements Plan — Unit 2: Product Microservice

---

## Execution Checklist

- [x] Step 1: Answer NFR questions (user fills [Answer]: tags below)
- [x] Step 2: Analyze answers — NO ambiguities
- [ ] Step 3: Generate nfr-requirements.md
- [ ] Step 4: Generate tech-stack-decisions.md
- [x] Step 5: Present for approval — user pre-approved with "Approve and proceed"

---

## Already Decided (carried from Unit 1 + requirements.md)

| NFR | Decision |
|---|---|
| API response time | < 500ms all endpoints; PLP target < 800ms (heavier query) |
| Uptime | 99.9% |
| Runtime | Python 3.11 + FastAPI |
| Database | PostgreSQL 15 on AWS RDS |
| Deployment | Docker on AWS EC2 |
| Security | All 15 SECURITY rules enforced |
| Test coverage | 80% minimum |
| EC2 sizing | t3.large (2 vCPU, 8 GB) — Product Service handles highest read traffic |
| Caching | Redis for PLP filter results (5-min TTL) — reduces DB load on repeated filter combos |

## NFR Question

## Question 1
The Product Service handles the heaviest read traffic (every page load). Should PLP query results be cached in Redis?

A) Yes — cache PLP results keyed by filter hash + sort + page (5-min TTL); invalidate on any product/category update
B) No — rely on PostgreSQL indexes + connection pooling; no Redis caching for MVP
C) Other (please describe after [Answer]: tag below)

[Answer]: A
