# Functional Design Plan — Unit 7: Admin Microservice
# sabhyakriti-admin-service

---

## Execution Checklist

- [ ] Step 1: Answer questions (user fills [Answer]: tags below)
- [ ] Step 2: Analyze answers
- [ ] Step 3: Generate artifacts + code
- [ ] Step 4: Present for approval

---

## Context Summary

Unit 7 is an aggregation/BFF layer for the Admin Panel.
It has NO own domain entities (no DB schema) — it reads/writes via other service APIs.
Aggregates: Auth (users), Product (catalog/inventory), Order (orders/returns),
Payment (revenue), Cart (coupons).
Provides: admin dashboard KPIs, sales reports, customer management, bulk product upload
coordination, coupon management.
Requirements: FR-ADM-01 to FR-ADM-11.

---

## Business Logic Questions

Please fill in the letter choice after each `[Answer]:` tag and let me know when done.

---

## Question 1
What default time period should the admin dashboard KPIs show?

A) Last 7 days — rolling 7-day window for revenue, orders, new customers
B) Last 30 days — rolling 30-day window (more representative)
C) Today + month-to-date — two KPI cards: today's numbers and this month's total
D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 2
Should sales reports be downloadable (exported), or view-only in the admin panel?

A) View-only — charts and tables displayed in UI; no CSV/PDF export
B) Downloadable CSV — admin can export the report data as a CSV file
C) Both — view in UI and download as CSV
D) Other (please describe after [Answer]: tag below)

[Answer]: B
