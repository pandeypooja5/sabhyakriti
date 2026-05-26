# Unit of Work — Requirements Map
# Sabhyakriti — Saree eCommerce Website

Note: User Stories stage was skipped. This document maps functional requirements (FR-* IDs
from requirements.md) and non-functional requirements (NFR-* IDs) to each unit of work.

---

## Unit 1: Auth Microservice (`sabhyakriti-auth-service`)

| Req ID | Requirement Summary |
|---|---|
| FR-AUTH-01 | User registration with email and password |
| FR-AUTH-02 | User login with email and password |
| FR-AUTH-03 | Google OAuth 2.0 social login |
| FR-AUTH-04 | Facebook OAuth social login |
| FR-AUTH-05 | Phone number + OTP login (SMS) |
| FR-AUTH-06 | Forgot password / reset password via email link |
| FR-AUTH-07 | Email verification on registration |
| FR-AUTH-08 | JWT-based session management with refresh tokens |
| FR-AUTH-09 | Logout invalidates session server-side |
| FR-AUTH-10 | MFA supported for admin accounts (mandatory) |
| FR-ACC-01 | User profile page — edit name, email, phone, profile picture |
| NFR-SEC-12 | Adaptive password hashing, brute-force protection, session management |
| NFR-SEC-17 | Rate limiting on auth endpoints |

---

## Unit 2: Product Microservice (`sabhyakriti-product-service`)

| Req ID | Requirement Summary |
|---|---|
| FR-PLP-01 | Display grid/list of saree products with product cards |
| FR-PLP-02 | Product card: thumbnail, name, price, brief description |
| FR-PLP-03 | Category filter: Fabric, Occasion, Region/Origin (3 dimensions) |
| FR-PLP-04 | Fabric categories: Silk, Cotton, Georgette, Chiffon, Chanderi, etc. |
| FR-PLP-05 | Occasion categories: Bridal, Party, Casual, Festive, Office, etc. |
| FR-PLP-06 | Region/Origin categories: Banarasi, Kanjivaram, Bandhani, etc. |
| FR-PLP-07 | Multi-filter support (multiple dimensions simultaneously) |
| FR-PLP-08 | Search bar by name, fabric, keywords |
| FR-PLP-09 | Sort: Price Low-High, Price High-Low, Newest, Most Popular |
| FR-PLP-10 | Pagination for product listing |
| FR-PLP-12 | Product count displayed |
| FR-PDP-01 | Image gallery (multiple product images) |
| FR-PDP-03 | Thumbnail strip for switching images |
| FR-PDP-04 | Product name, SKU, price, discount |
| FR-PDP-05 | Product description |
| FR-PDP-06 | Key attributes: fabric, color, pattern, blouse, dimensions |
| FR-PDP-07 | Size guide section |
| FR-PDP-08 | Care instructions |
| FR-PDP-09 | Stock availability indicator |
| FR-PDP-12 | Customer reviews and ratings section |
| FR-PDP-13 | Related products |
| FR-ADM-03 | Admin: add, edit, delete products with images and attributes |
| FR-ADM-04 | Admin: bulk product upload via CSV |
| FR-ADM-05 | Admin: category management (Fabric, Occasion, Region) |
| FR-ADM-06 | Admin: inventory stock quantity update |
| FR-ADM-12 | Admin: image upload to AWS S3 |

---

## Unit 3: Cart & Wishlist Microservice (`sabhyakriti-cart-service`)

| Req ID | Requirement Summary |
|---|---|
| FR-PLP-11 | "Add to Wishlist" button on product cards |
| FR-CART-01 | Add/remove products from cart |
| FR-CART-02 | Update quantity in cart |
| FR-CART-03 | Cart persists across sessions (logged-in users) |
| FR-CART-04 | Cart summary: subtotal, taxes, shipping, total |
| FR-CART-05 | Coupon/discount code application |
| FR-ACC-06 | Wishlist page — view, manage, add to cart |
| FR-ADM-10 | Admin: coupon/discount code management |

---

## Unit 4: Order Microservice (`sabhyakriti-order-service`)

| Req ID | Requirement Summary |
|---|---|
| FR-CART-06 | Checkout step 1: delivery address selection or new entry |
| FR-CART-07 | Checkout step 2: payment method selection |
| FR-CART-08 | Checkout step 3: order review and place order |
| FR-CART-09 | Order confirmation page with order ID |
| FR-CART-10 | Order confirmation email sent to customer |
| FR-ORD-01 | Order status lifecycle: Pending → Confirmed → Shipped → Delivered |
| FR-ORD-02 | Customer views real-time order status |
| FR-ORD-03 | Shipment tracking number / courier link on order detail page |
| FR-ORD-04 | Customer can cancel order (before shipped) |
| FR-ORD-05 | Return request flow (within return window) |
| FR-ORD-06 | Refund status tracking |
| FR-ORD-07 | Email notifications on every order status change |
| FR-ORD-08 | SMS notifications for shipped and delivered |
| FR-ORD-09 | Invoice PDF generation and download |
| FR-ACC-04 | Order history listing with status, date, total |
| FR-ACC-05 | View individual order details (items, tracking, invoice) |
| FR-ACC-02 | Address book — save, edit, delete multiple delivery addresses |
| FR-ACC-03 | Default address designation |
| FR-ADM-07 | Admin: view all orders, update status, add tracking number |
| FR-ADM-09 | Admin: returns and refund management |

---

## Unit 5: Payment Microservice (`sabhyakriti-payment-service`)

| Req ID | Requirement Summary |
|---|---|
| FR-PAY-01 | Razorpay: card, net banking, wallets |
| FR-PAY-02 | UPI payment support via Razorpay |
| FR-PAY-03 | Cash on Delivery (COD) with pin code availability check |
| FR-PAY-04 | Payment success and failure handling |
| FR-PAY-05 | Webhook handling for Razorpay payment status updates |
| FR-PAY-06 | Payment receipt stored and emailed to customer |
| FR-PAY-07 | Refund initiation via Razorpay Refund API |

---

## Unit 6: Notification Microservice (`sabhyakriti-notification-service`)

| Req ID | Requirement Summary |
|---|---|
| FR-AUTH-07 | Email verification email on registration |
| FR-AUTH-06 | Password reset email |
| FR-CART-10 | Order confirmation email |
| FR-ORD-07 | Email notifications: order placed, shipped, delivered, cancelled, refunded |
| FR-ORD-08 | SMS notifications: shipped, delivered |
| FR-AUTH-05 | OTP SMS for phone number login |
| FR-PAY-06 | Payment receipt email |
| NFR-SEC-03 | Structured logging to CloudWatch |
| NFR-SEC-14 | Alerting and log retention |

---

## Unit 7: Admin Microservice (`sabhyakriti-admin-service`)

| Req ID | Requirement Summary |
|---|---|
| FR-ADM-01 | Secure admin login with MFA |
| FR-ADM-02 | Admin dashboard: sales summary, recent orders, low-stock alerts |
| FR-ADM-08 | Customer management: list customers, order history per customer |
| FR-ADM-11 | Sales reports: revenue by date range, top products, category performance |

Note: Product CRUD, order management, coupon management, and returns handled in U2, U4, U5 respectively. U7 aggregates and exposes these via the admin API.

---

## Unit 8: AWS Infrastructure (`sabhyakriti-infra`)

| Req ID | Requirement Summary |
|---|---|
| NFR-SCAL-01 | AWS EC2 Auto Scaling Group |
| NFR-SCAL-02 | AWS RDS PostgreSQL with read replica |
| NFR-SCAL-03 | AWS S3 + CloudFront CDN |
| NFR-SCAL-04 | 99.9% uptime target |
| NFR-SEC-01 | Encryption at rest (RDS, S3) and in transit (TLS 1.2+) |
| NFR-SEC-02 | Load balancer and API Gateway access logging |
| NFR-SEC-06 | Least-privilege IAM roles |
| NFR-SEC-07 | Restrictive security groups, private subnets |
| NFR-SEC-15 | Log retention minimum 90 days, CloudWatch alarms |
| NFR-PERF-03 | CloudFront CDN for image serving |
| NFR-TEST-06 | CI/CD pipeline (GitHub Actions) per service |

---

## Unit 9: Frontend (`sabhyakriti-frontend`)

| Req ID | Requirement Summary |
|---|---|
| FR-PLP-01 to FR-PLP-13 | All PLP UI: product grid, filters, search, sort, pagination, wishlist icon |
| FR-PDP-01 to FR-PDP-15 | All PDP UI: image gallery, lightbox/maximize, attributes, reviews, related products, breadcrumb, share |
| FR-AUTH-01 to FR-AUTH-10 | Auth UI: all login/register forms and OAuth flows |
| FR-CART-01 to FR-CART-10 | Cart + Checkout UI: cart management, multi-step checkout, order confirmation |
| FR-ORD-01 to FR-ORD-09 | Order UI: history, detail, status timeline, cancel modal, return modal, invoice download |
| FR-ACC-01 to FR-ACC-07 | Account UI: profile, address book, order history, wishlist, account deletion |
| FR-ADM-01 to FR-ADM-12 | Admin Panel UI: all admin pages |
| FR-PAY-01 to FR-PAY-07 | Payment UI: Razorpay widget, UPI selector, COD option |
| NFR-UX-01 | Responsive design (desktop, tablet, mobile) |
| NFR-UX-02 | WCAG 2.1 Level AA accessibility |
| NFR-UX-03 | SEO-friendly URLs and meta tags |
| NFR-SEC-04 | HTTP security headers enforced |
| NFR-PERF-01 | PLP page loads within 3 seconds |
| NFR-PERF-02 | PDP page loads within 2 seconds |

---

## Requirements Coverage Summary

| Unit | FR Count | NFR Count | Coverage |
|---|---|---|---|
| U1 Auth | 13 | 2 | Auth + profile |
| U2 Product | 22 | 0 | Catalog, PLP, PDP backend, admin product/category |
| U3 Cart | 8 | 0 | Cart + wishlist + coupons |
| U4 Order | 16 | 0 | Full order lifecycle + addresses |
| U5 Payment | 7 | 0 | All payment methods + webhooks + refunds |
| U6 Notification | 8 | 2 | All transactional notifications |
| U7 Admin | 4 | 0 | Dashboard + reports + customers (aggregation) |
| U8 Infra | 0 | 10 | All infrastructure + CI/CD NFRs |
| U9 Frontend | All FR-PLP/PDP/AUTH/CART/ORD/ACC/ADM/PAY | 4 | All UI + UX NFRs |
| **Total** | **~78 FR** | **~18 NFR** | **100% requirements covered** |
