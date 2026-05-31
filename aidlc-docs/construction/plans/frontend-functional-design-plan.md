# Functional Design Plan — Unit 9: Frontend
# sabhyakriti-frontend

---

## Execution Checklist

- [ ] Step 1: Answer questions (user fills [Answer]: tags below)
- [ ] Step 2: Analyze answers
- [ ] Step 3: Generate functional design + component hierarchy
- [ ] Step 4: Generate code
- [ ] Step 5: Present for approval

---

## Context Summary

Unit 9 is the React 18 frontend (Vite + TypeScript + Tailwind CSS + shadcn/ui + Redux Toolkit).
All 9 repositories will be complete after this unit.
Brand colours: saffron #FF6B2B, deep teal #1B4B5A (from email templates).
Tech stack decided: React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui, Redux Toolkit,
React Router v6, Axios, Razorpay JS SDK.

Most design decisions are clear from requirements and application design.
A few UI/UX decisions remain open:

---

## Question 1
Should the website have a dedicated Homepage (hero banner + featured/new products section)
before the PLP, or should the root URL `/` open directly to the PLP?

A) Dedicated homepage — hero banner with brand story + "Shop Now" CTA, featured sarees section, new arrivals, category shortcuts — then `/sarees` for the full PLP
B) PLP is the homepage — root URL `/` renders the full product listing directly (simpler, faster path to products)
C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 2
For the Product Detail Page image gallery on mobile — should zooming in on the image be supported?

A) Yes — pinch-to-zoom on mobile + click-to-zoom lightbox on desktop (already planned as "maximize feature")
B) No — full-screen lightbox on click is sufficient; no pinch-to-zoom needed
C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 3
Should the website support a Dark Mode toggle?

A) No — light mode only (saffron + teal theme); simpler to build and maintain
B) Yes — light/dark toggle stored in user preferences
C) Other (please describe after [Answer]: tag below)

[Answer]: A
