# Unit of Work Plan
# Sabhyakriti — Saree eCommerce Website

---

## Execution Checklist

- [x] Step 1: Answer decomposition questions (user fills [Answer]: tags below)
- [x] Step 2: Analyze answers — NO contradictions. Microservices + solo dev noted as valid choice.
- [x] Step 3: Generate unit-of-work.md
- [x] Step 4: Generate unit-of-work-dependency.md
- [x] Step 5: Generate unit-of-work-story-map.md
- [x] Step 6: Present for approval

---

## Proposed Units (from Workflow Planning)

The 8 units already defined are:

| # | Unit Name | Core Scope |
|---|---|---|
| 1 | Foundation & Auth | DB schema, user model, all 4 auth methods, JWT sessions |
| 2 | Product Catalog & PLP | Product model, categories (3 types), PLP filters/search/sort/pagination |
| 3 | Product Detail Page | PDP image gallery + lightbox, attributes, reviews, related products |
| 4 | Cart & Wishlist | Cart CRUD, wishlist, coupon/discount engine |
| 5 | Order Management | Full order lifecycle, cancel/return/refund, email+SMS notifications |
| 6 | Payment Integration | Razorpay, UPI, COD, webhooks, refund API |
| 7 | Admin Panel | Full admin: products, orders, inventory, customers, coupons, reports |
| 8 | AWS Infrastructure | VPC, EC2, ALB, RDS, S3, CloudFront, SES, SNS, CloudWatch, IAM, CI/CD |

---

## Decomposition Questions

Please fill in the letter choice after each `[Answer]:` tag and let me know when done.

---

## Question 1
How will the FastAPI backend be deployed — as a single application or multiple services?

A) Single FastAPI monolith — one app with modular DDD structure (routers per domain); simpler to deploy and operate for a startup
B) Microservices — each domain (auth, products, orders, payments) as a separate FastAPI service
C) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 2
How should each unit of work be scoped for code generation — what does one unit produce?

A) Full-stack per unit — each unit generates both the backend API code AND the corresponding React frontend components together
B) Backend-first — generate all backend units first (Units 1–7), then generate frontend separately as Unit 9
C) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 3
Who will be building this — a solo developer or a team?

A) Solo developer — one person implementing all units sequentially
B) Small team (2–3 developers) — can work on different units somewhat in parallel after Unit 1 is done
C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 4
Which units form the Minimum Viable Product (MVP) that needs to go live first?

A) Units 1–6 + Unit 8 — Foundation, Catalog, PDP, Cart, Orders, Payments, Infrastructure (Admin Panel comes post-launch as Unit 7)
B) All 8 units — full platform including Admin Panel before launch
C) Units 1–4 + Unit 8 — Foundation, Catalog, PDP, Cart, Infrastructure (Orders + Payments come in a follow-up release)
D) Other (please describe after [Answer]: tag below)

[Answer]: B
