# Functional Design Plan — Unit 2: Product Microservice
# sabhyakriti-product-service

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

Unit 2 owns: Product, Category, ProductCategory, ProductImage, Review entities.
Handles: product catalog, 3-dimension category system (Fabric/Occasion/Region), PLP
filtering/search/sort/pagination, PDP detail, product reviews, S3 presigned image upload,
admin product CRUD, bulk CSV import.
Requirements: FR-PLP-01 to FR-PLP-13, FR-PDP-01 to FR-PDP-15, FR-ADM-03 to FR-ADM-06, FR-ADM-12.

---

## Business Logic Questions

Please fill in the letter choice after each `[Answer]:` tag and let me know when done.

---

## Question 1
When a customer applies multiple category filters on the PLP (e.g., Fabric=Silk AND Occasion=Bridal), how should they combine?

A) AND logic — product must match ALL selected filters across ALL dimensions (Silk AND Bridal)
B) Within-dimension OR, cross-dimension AND — e.g., (Silk OR Cotton) AND (Bridal OR Party)
C) Full OR — show products matching ANY selected filter
D) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 2
What type of search should the PLP search bar use?

A) Simple ILIKE / pattern match — search in product name, fabric type, description (no search engine needed)
B) PostgreSQL full-text search (tsvector/tsquery) — ranked results, handles partial words, no extra infra
C) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 3
What is the "Low Stock" threshold for the stock availability indicator on PDP?

A) Low Stock when quantity ≤ 5 units
B) Low Stock when quantity ≤ 10 units
C) Low Stock when quantity ≤ 20 units
D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 4
Should product reviews require a verified purchase (user must have ordered and received the product)?

A) Yes — only customers with a DELIVERED order containing that product can submit a review
B) No — any registered user can review any product
C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 5
How should product slugs (used in SEO-friendly URLs like `/sarees/kanjivaram-silk-red`) be generated?

A) Auto-generated from product name at creation — e.g., "Kanjivaram Silk Red" → "kanjivaram-silk-red"; append UUID suffix if collision
B) Admin manually specifies slug at product creation; validated for uniqueness
C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 6
How should the discount price work?

A) Admin sets both `price` (MRP/original) and `discount_price` (selling price) separately; frontend displays both with % savings calculated
B) Admin sets `price` and a `discount_percentage`; system calculates `discounted_price = price × (1 - discount_percentage/100)`
C) Other (please describe after [Answer]: tag below)

[Answer]: B
