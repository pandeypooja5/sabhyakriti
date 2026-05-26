# NFR Design Plan — Unit 1: Auth Microservice
# Sabhyakriti — Saree eCommerce Website

---

## Execution Checklist

- [ ] Step 1: Answer NFR design questions (user fills [Answer]: tags below)
- [ ] Step 2: Analyze answers
- [x] Step 3: Generate nfr-design-patterns.md
- [x] Step 4: Generate logical-components.md
- [x] Step 5: Present for approval

---

## Already Determined (no questions needed)

All NFR patterns are derivable directly from the NFR Requirements and decisions already made:
- Security patterns: from SECURITY-01 to SECURITY-15 + business rules
- Resilience patterns: retry + fail-open/fail-closed defined per service in nfr-requirements.md
- Rate limiting: Redis sliding window (already decided)
- Caching: Redis for tokens (already decided)
- Scaling: single t3.medium EC2 (already decided)

**No additional user input required.** Generating design artifacts directly.

- [x] Step 1: No questions needed — all inputs determined
- [x] Step 2: N/A
- [x] Step 3: Generate nfr-design-patterns.md
- [x] Step 4: Generate logical-components.md
- [x] Step 5: Present for approval
