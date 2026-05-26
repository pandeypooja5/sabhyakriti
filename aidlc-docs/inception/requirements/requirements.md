# Requirements Document
# Sabhyakriti — Saree eCommerce Website

---

## Intent Analysis

| Field | Value |
|---|---|
| **User Request** | Build a full eCommerce website exclusively for Sarees with PLP, PDP, Admin Panel, and Payment integration |
| **Request Type** | New Project (Greenfield) |
| **Scope Estimate** | System-wide — multiple components (frontend, backend, database, admin panel, payment gateway) |
| **Complexity Estimate** | Complex — full eCommerce platform with authentication, payments, orders, admin, and AWS deployment |
| **Depth Level** | Comprehensive |

---

## 1. Functional Requirements

### 1.1 Product Listing Page (PLP)

| ID | Requirement |
|---|---|
| FR-PLP-01 | Display a grid/list of saree products with product cards |
| FR-PLP-02 | Each product card shows: thumbnail image, product name, price, and brief description |
| FR-PLP-03 | Category filter sidebar with three dimensions: Fabric, Occasion, and Region/Origin |
| FR-PLP-04 | Fabric categories: Silk, Cotton, Georgette, Chiffon, Chanderi, Linen, Net, etc. |
| FR-PLP-05 | Occasion categories: Bridal, Party, Casual, Festive, Office, Wedding, etc. |
| FR-PLP-06 | Region/Origin categories: Banarasi, Kanjivaram, Bandhani, Pochampally, Paithani, Sambalpuri, etc. |
| FR-PLP-07 | Multi-filter support — user can apply filters from multiple dimensions simultaneously |
| FR-PLP-08 | Search bar to search products by name, fabric, or keywords |
| FR-PLP-09 | Sort options: Price Low-High, Price High-Low, Newest First, Most Popular |
| FR-PLP-10 | Pagination or infinite scroll for product listing |
| FR-PLP-11 | "Add to Wishlist" button visible on each product card |
| FR-PLP-12 | Product count displayed (e.g., "Showing 24 of 120 products") |
| FR-PLP-13 | Clicking a product card navigates to the Product Detail Page (PDP) |

### 1.2 Product Detail Page (PDP)

| ID | Requirement |
|---|---|
| FR-PDP-01 | Image gallery with multiple product images |
| FR-PDP-02 | Image maximize/lightbox feature — click to view full-screen with zoom |
| FR-PDP-03 | Thumbnail strip for switching between images |
| FR-PDP-04 | Product name, SKU/ID, and price (with any discount shown) |
| FR-PDP-05 | Product description (fabric story, weaving details, etc.) |
| FR-PDP-06 | Key attributes: Fabric type, Color, Pattern, Blouse included (Y/N), Length/dimensions |
| FR-PDP-07 | Size guide section or popup |
| FR-PDP-08 | Care instructions section |
| FR-PDP-09 | Stock availability indicator (In Stock / Out of Stock / Low Stock) |
| FR-PDP-10 | "Add to Cart" and "Buy Now" buttons |
| FR-PDP-11 | "Add to Wishlist" button |
| FR-PDP-12 | Customer reviews and ratings section (submit review, star rating) |
| FR-PDP-13 | Related products carousel/section |
| FR-PDP-14 | Breadcrumb navigation (Home > Category > Product Name) |
| FR-PDP-15 | Share product on social media |

### 1.3 User Authentication

| ID | Requirement |
|---|---|
| FR-AUTH-01 | User registration with email and password |
| FR-AUTH-02 | User login with email and password |
| FR-AUTH-03 | Google OAuth 2.0 social login |
| FR-AUTH-04 | Facebook OAuth social login |
| FR-AUTH-05 | Phone number + OTP login (SMS via Twilio or AWS SNS) |
| FR-AUTH-06 | Forgot password / reset password flow via email link |
| FR-AUTH-07 | Email verification on registration |
| FR-AUTH-08 | JWT-based session management with refresh tokens |
| FR-AUTH-09 | Logout invalidates session server-side |
| FR-AUTH-10 | MFA supported for admin accounts (mandatory) |

### 1.4 User Account & Profile

| ID | Requirement |
|---|---|
| FR-ACC-01 | User profile page with editable name, email, phone number, and profile picture |
| FR-ACC-02 | Address book — save, edit, delete multiple delivery addresses |
| FR-ACC-03 | Default address designation |
| FR-ACC-04 | Order history listing with status, date, total |
| FR-ACC-05 | View individual order details (items, tracking, invoice) |
| FR-ACC-06 | Wishlist page — view, manage, and add wishlist items to cart |
| FR-ACC-07 | Account deletion / data export request |

### 1.5 Shopping Cart & Checkout

| ID | Requirement |
|---|---|
| FR-CART-01 | Add/remove products from cart |
| FR-CART-02 | Update quantity in cart |
| FR-CART-03 | Cart persists across sessions (saved in database for logged-in users) |
| FR-CART-04 | Cart summary with item subtotal, taxes, shipping charges, and final total |
| FR-CART-05 | Coupon/discount code application |
| FR-CART-06 | Checkout step 1: Delivery address selection or new address entry |
| FR-CART-07 | Checkout step 2: Payment method selection (Razorpay / UPI / COD) |
| FR-CART-08 | Checkout step 3: Order review and place order confirmation |
| FR-CART-09 | Order confirmation page with order ID after successful placement |
| FR-CART-10 | Order confirmation email sent to customer |

### 1.6 Payment Integration

| ID | Requirement |
|---|---|
| FR-PAY-01 | Razorpay integration for card (credit/debit), net banking, and wallets |
| FR-PAY-02 | UPI payment support via Razorpay UPI or direct UPI |
| FR-PAY-03 | Cash on Delivery (COD) option with COD availability check by pin code |
| FR-PAY-04 | Payment success and failure handling with appropriate user feedback |
| FR-PAY-05 | Webhook handling for Razorpay payment status updates |
| FR-PAY-06 | Payment receipt stored in database and emailed to customer |
| FR-PAY-07 | Refund initiation through admin panel (processed via Razorpay refund API) |

### 1.7 Order Management

| ID | Requirement |
|---|---|
| FR-ORD-01 | Order placed → status: Pending → Confirmed → Shipped → Delivered |
| FR-ORD-02 | Customer can view real-time order status |
| FR-ORD-03 | Shipment tracking number / courier link displayed on order detail page |
| FR-ORD-04 | Customer can cancel order (before it is shipped) |
| FR-ORD-05 | Return request flow — customer initiates return within return window (configurable) |
| FR-ORD-06 | Refund status tracking |
| FR-ORD-07 | Email notifications at every order status change (order placed, shipped, delivered, cancelled, refunded) |
| FR-ORD-08 | SMS notifications for key order events (shipped, delivered) |
| FR-ORD-09 | Invoice generation and download (PDF) per order |

### 1.8 Admin Panel

| ID | Requirement |
|---|---|
| FR-ADM-01 | Secure admin login with MFA (separate from customer login) |
| FR-ADM-02 | Dashboard with sales summary, recent orders, low-stock alerts |
| FR-ADM-03 | Product management: add, edit, delete products with images, pricing, and attributes |
| FR-ADM-04 | Bulk product upload via CSV |
| FR-ADM-05 | Category management: add/edit/delete fabric, occasion, and regional categories |
| FR-ADM-06 | Inventory management: update stock quantities, set low-stock threshold alerts |
| FR-ADM-07 | Order management: view all orders, update order status, add tracking number |
| FR-ADM-08 | Customer management: view customer list, order history per customer |
| FR-ADM-09 | Returns and refund management: approve/reject return requests, initiate refunds |
| FR-ADM-10 | Coupon/discount code management: create, edit, deactivate coupons |
| FR-ADM-11 | Basic sales reports: revenue by date range, top-selling products, category performance |
| FR-ADM-12 | Image upload to AWS S3 for product images |

---

## 2. Non-Functional Requirements

### 2.1 Performance

| ID | Requirement |
|---|---|
| NFR-PERF-01 | PLP page loads within 3 seconds on a standard broadband connection |
| NFR-PERF-02 | PDP page loads within 2 seconds |
| NFR-PERF-03 | Product images served via AWS CloudFront CDN with compression |
| NFR-PERF-04 | API response times under 500ms for standard operations |
| NFR-PERF-05 | Database queries optimized with indexes on frequently queried columns |

### 2.2 Security

Security is **fully enforced** per the Security Baseline Extension (15 rules: SECURITY-01 through SECURITY-15).

| ID | Requirement |
|---|---|
| NFR-SEC-01 | All data at rest encrypted (RDS, S3) — SECURITY-01 |
| NFR-SEC-02 | All data in transit over TLS 1.2+ — SECURITY-01 |
| NFR-SEC-03 | Load balancer and API Gateway access logging enabled — SECURITY-02 |
| NFR-SEC-04 | Structured application logging to AWS CloudWatch — SECURITY-03 |
| NFR-SEC-05 | HTTP security headers enforced (CSP, HSTS, X-Frame-Options, etc.) — SECURITY-04 |
| NFR-SEC-06 | All API inputs validated and sanitized — SECURITY-05 |
| NFR-SEC-07 | Least-privilege IAM roles for all AWS resources — SECURITY-06 |
| NFR-SEC-08 | Restrictive security groups; private subnets for DB and app servers — SECURITY-07 |
| NFR-SEC-09 | JWT auth enforced on all private endpoints; IDOR prevention — SECURITY-08 |
| NFR-SEC-10 | No default credentials; generic error messages in production — SECURITY-09 |
| NFR-SEC-11 | Dependency lock files committed; vulnerability scanning in CI/CD — SECURITY-10 |
| NFR-SEC-12 | Auth, payment, and authorization logic isolated in dedicated modules — SECURITY-11 |
| NFR-SEC-13 | Adaptive password hashing; brute-force protection on login — SECURITY-12 |
| NFR-SEC-14 | SRI hashes on external CDN scripts; critical data change audit log — SECURITY-13 |
| NFR-SEC-15 | Alerting on auth failures; log retention minimum 90 days — SECURITY-14 |
| NFR-SEC-16 | Fail-closed error handling; global exception handler — SECURITY-15 |
| NFR-SEC-17 | Rate limiting on all public-facing API endpoints — SECURITY-11 |

### 2.3 Scalability & Availability

| ID | Requirement |
|---|---|
| NFR-SCAL-01 | AWS EC2 Auto Scaling Group for application servers |
| NFR-SCAL-02 | AWS RDS PostgreSQL with read replica for read-heavy PLP/PDP queries |
| NFR-SCAL-03 | AWS S3 for product image storage; CloudFront for CDN delivery |
| NFR-SCAL-04 | Target 99.9% uptime (three nines) |

### 2.4 Usability & Accessibility

| ID | Requirement |
|---|---|
| NFR-UX-01 | Fully responsive design — desktop, tablet, and mobile |
| NFR-UX-02 | WCAG 2.1 Level AA accessibility compliance |
| NFR-UX-03 | SEO-friendly URLs and meta tags for product pages |
| NFR-UX-04 | Fast checkout — guest checkout not required (registration mandatory) |

### 2.5 Testing (Property-Based Testing — Fully Enforced)

| ID | Requirement |
|---|---|
| NFR-TEST-01 | Unit tests for all business logic with minimum 80% code coverage |
| NFR-TEST-02 | Property-based tests (PBT) for payment calculations, discount logic, pricing, and order total computations |
| NFR-TEST-03 | PBT for serialization round-trips (product data, order data) |
| NFR-TEST-04 | Integration tests for Razorpay payment flow (sandbox) |
| NFR-TEST-05 | API integration tests for all REST endpoints |
| NFR-TEST-06 | End-to-end tests for critical user flows: register, browse, add to cart, checkout, pay |

---

## 3. Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | React.js (with React Router, Context API or Redux) |
| **Backend** | Python 3.11+ / FastAPI |
| **Database** | PostgreSQL 15+ (AWS RDS) |
| **ORM** | SQLAlchemy + Alembic (migrations) |
| **Auth** | FastAPI JWT + OAuth2 (Google, Facebook), Twilio for OTP |
| **Payment** | Razorpay SDK (Python + React) |
| **File Storage** | AWS S3 + CloudFront CDN |
| **Hosting** | AWS EC2 (app), AWS RDS (DB), AWS S3 (assets) |
| **Email** | AWS SES (transactional emails) |
| **SMS** | AWS SNS or Twilio (OTP, order notifications) |
| **Monitoring** | AWS CloudWatch |
| **CI/CD** | GitHub Actions |
| **Currency** | INR (Indian Rupee) |
| **Market** | India only |

---

## 4. Business Context

| Field | Value |
|---|---|
| **Brand Name** | Sabhyakriti |
| **Business Type** | D2C (Direct-to-Consumer) eCommerce — Sarees only |
| **Target Market** | India — INR currency |
| **Payment Methods** | Razorpay (card/net banking/wallet), UPI, Cash on Delivery |
| **Key Success Criteria** | Customers can browse, discover, and purchase sarees seamlessly with a trustworthy checkout and payment experience |

---

## 5. Extension Configuration

| Extension | Enabled | Decided At |
|---|---|---|
| Security Baseline (SECURITY-01 to SECURITY-15) | Yes | Requirements Analysis |
| Property-Based Testing (PBT) | Yes — Full enforcement | Requirements Analysis |
