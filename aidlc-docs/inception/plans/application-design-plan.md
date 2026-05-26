# Application Design Plan
# Sabhyakriti — Saree eCommerce Website

---

## Execution Checklist

- [x] Step 1: Answer design questions (user fills [Answer]: tags below)
- [x] Step 2: Analyze answers for ambiguities — NO ambiguities detected
- [x] Step 3: Generate components.md
- [x] Step 4: Generate component-methods.md
- [x] Step 5: Generate services.md
- [x] Step 6: Generate component-dependency.md
- [x] Step 7: Generate consolidated application-design.md
- [x] Step 8: Present for approval

---

## Design Questions

Please answer each question by filling in the letter choice after the `[Answer]:` tag.
Let me know when done.

---

## Question 1
What UI component library / CSS framework should be used for the React frontend?

A) Tailwind CSS + shadcn/ui — utility-first CSS with pre-built accessible components, highly customizable
B) Material UI (MUI) — comprehensive React component library with Material Design, fast to build with
C) Ant Design — enterprise-grade React UI with rich components (data tables, forms, etc. — good for Admin Panel)
D) Chakra UI — accessible, themeable, modern component library
E) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 2
What state management approach should be used in the React frontend?

A) Redux Toolkit — industry standard, excellent for complex cart/order state, good dev tools
B) Zustand — lightweight, minimal boilerplate, easy to learn
C) React Context API + useReducer — built-in, no extra dependencies, sufficient for this scale
D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 3
How should the project be organized (repository structure)?

A) Monorepo — single repository with `/frontend` and `/backend` folders, shared tooling and CI/CD
B) Separate repositories — `sabhyakriti-frontend` and `sabhyakriti-backend` as independent repos
C) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 4
What backend architectural pattern should be used in FastAPI?

A) Layered architecture — Router → Service → Repository → Database (clean separation of concerns)
B) Domain-driven design (DDD) — domain models, application services, infrastructure adapters
C) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 5
How should product images be handled on upload and display?

A) Upload to AWS S3 directly from backend, serve via CloudFront CDN — recommended for production
B) Upload to AWS S3 directly from frontend (presigned URLs), serve via CloudFront CDN — faster upload
C) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 6
Should the Admin Panel be a separate React app or integrated into the same frontend app?

A) Integrated — same React app with role-based routing (e.g., `/admin/*` routes protected by admin role)
B) Separate app — a second React SPA at a different domain/subdomain (e.g., admin.sabhyakriti.com)
C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 7
How should real-time order status updates be handled on the customer-facing side?

A) Polling — customer's browser polls the API every 30 seconds for status changes (simple, no extra infra)
B) Server-Sent Events (SSE) — server pushes status updates to the browser (lightweight push)
C) WebSockets — bidirectional real-time connection (overkill for order status, but future-proof)
D) No real-time needed — customer refreshes the page or receives email/SMS (simplest approach)
E) Other (please describe after [Answer]: tag below)

[Answer]: A
