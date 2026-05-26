# Services Definition
# Sabhyakriti — Saree eCommerce Website

---

## Service Architecture Overview

```
Frontend (React)
    |
    | HTTP (REST/JSON over TLS)
    v
FastAPI Presentation Layer (Routers + Middleware)
    |
    v
Application Layer (Application Services — Use Cases)
    |
    +---> Domain Layer (Entities + Domain Services + Repository Interfaces)
    |
    +---> Infrastructure Layer (Repository Implementations + External Adapters)
                |
                +---> PostgreSQL (via SQLAlchemy)
                +---> AWS S3, SES, SNS, CloudWatch
                +---> Razorpay API
                +---> Google / Facebook OAuth
                +---> Twilio SMS
```

---

## 1. Application Services (Use Case Orchestrators)

### AuthApplicationService

**Purpose**: Orchestrates all authentication and session management flows.

**Key Orchestrations**:
- On email registration: hash password → create User entity → persist → send verification email via NotificationApplicationService
- On OAuth login: call OAuth adapter → find or create User by provider ID → issue JWT tokens
- On OTP login: send OTP via SMS adapter → store hashed OTP with TTL → verify on submit → issue tokens
- On token refresh: validate refresh token from Redis/DB → issue new access token
- On logout: revoke refresh token from store

**Dependencies**:
- `IUserRepository`, `GoogleOAuthAdapter`, `FacebookOAuthAdapter`, `TwilioSMSAdapter`, `AWSSESAdapter`
- `PricingDomainService` (N/A — not used here)

---

### ProductApplicationService

**Purpose**: Manages the full product catalog lifecycle including PLP querying and admin CRUD.

**Key Orchestrations**:
- PLP list: accept filters/search/sort/page → build query via IProductRepository → return paginated DTOs
- PDP detail: fetch product + images + categories + average rating → compose ProductDetailDTO
- Admin create: validate admin role → create Product entity → persist → return DTO
- Image upload flow: generate S3 presigned URL → return to frontend (frontend uploads directly) → frontend calls `confirm_image_upload` → store S3 key + CloudFront URL
- Bulk import: parse CSV rows → validate each → batch persist → return success/failure report

**Dependencies**:
- `IProductRepository`, `ICategoryRepository`, `AWSS3Adapter`, `AWSCloudFrontAdapter`

---

### CategoryApplicationService

**Purpose**: Manages the three category dimensions (Fabric, Occasion, Region).

**Key Orchestrations**:
- List: optionally filter by type → return sorted category list
- Create/Update: validate admin role → persist → return DTO
- Delete: check no active products in category → delete

**Dependencies**:
- `ICategoryRepository`, `IProductRepository` (for delete guard)

---

### CartApplicationService

**Purpose**: Manages per-user shopping cart including coupon application and real-time pricing.

**Key Orchestrations**:
- Get cart: load cart items → fetch current product prices → call `PricingDomainService.calculate_cart_total` → return CartDTO with totals
- Add to cart: call `InventoryDomainService.check_availability` → upsert CartItem → recalculate totals
- Apply coupon: load coupon → call `PricingDomainService.validate_coupon` → persist applied_coupon on Cart → recalculate totals

**Dependencies**:
- `ICartRepository`, `IProductRepository`, `ICouponRepository`
- `PricingDomainService`, `InventoryDomainService`

---

### WishlistApplicationService

**Purpose**: Simple service managing per-user product wishlist.

**Key Orchestrations**:
- Add: idempotent upsert of WishlistItem
- Get: load wishlist items → join with product details → return DTO

**Dependencies**:
- `IWishlistRepository`, `IProductRepository`

---

### OrderApplicationService

**Purpose**: Orchestrates the full order lifecycle from creation to delivery and returns.

**Key Orchestrations**:
- Create order:
  1. Load cart → validate via `OrderDomainService.validate_order_creation`
  2. Reserve stock via `InventoryDomainService.reserve_stock` (atomic DB transaction)
  3. Snapshot product prices into OrderItems
  4. Create Order + OrderItems in DB
  5. If COD: set status CONFIRMED immediately
  6. If Razorpay/UPI: set status PENDING, return order_id to frontend for payment flow
  7. Clear cart
  8. Trigger `NotificationApplicationService.send_order_confirmation`
- Cancel order: validate via `OrderDomainService.can_cancel` → release stock → set status CANCELLED → trigger notification
- Admin update status: advance status → set tracking number → trigger shipping/delivery notification
- Return request: validate via `OrderDomainService.can_return` → create ReturnRequest → notify admin

**Dependencies**:
- `IOrderRepository`, `ICartRepository`, `IProductRepository`, `IAddressRepository`
- `OrderDomainService`, `InventoryDomainService`
- `NotificationApplicationService`

---

### PaymentApplicationService

**Purpose**: Manages all payment operations through Razorpay and handles webhooks.

**Key Orchestrations**:
- Create Razorpay order: call `RazorpayAdapter.create_order(amount)` → persist Payment record (status=CREATED) → return Razorpay order_id + key to frontend
- Verify payment: receive razorpay_payment_id + signature from frontend → `RazorpayAdapter.verify_signature` → if valid: update Payment status=CAPTURED → update Order status=CONFIRMED → trigger order confirmation notification
- Webhook: validate Razorpay webhook signature → process event type (payment.captured, refund.processed) → update Payment/Order status accordingly
- Initiate refund: admin triggers → `RazorpayAdapter.create_refund(razorpay_payment_id, amount)` → update Payment status=REFUNDED → update Order status=REFUNDED → trigger notification

**Dependencies**:
- `IPaymentRepository`, `IOrderRepository`, `RazorpayAdapter`
- `NotificationApplicationService`

---

### ReviewApplicationService

**Purpose**: Manages customer product reviews.

**Key Orchestrations**:
- Submit review: verify user has a delivered order containing the product → create Review → update product average_rating in DB
- Delete review: verify ownership (customer) or admin role → delete → recalculate average_rating

**Dependencies**:
- `IReviewRepository`, `IOrderRepository`, `IProductRepository`

---

### AddressApplicationService

**Purpose**: Manages per-user address book.

**Key Orchestrations**:
- Add address: persist → if first address or `is_default=True`: call `set_default_address`
- Delete address: if deleting default: auto-assign default to most recent remaining address
- Set default: clear existing default flag on all user addresses → set new default

**Dependencies**:
- `IAddressRepository`

---

### NotificationApplicationService

**Purpose**: Centralized notification dispatcher — routes to email (SES) or SMS (Twilio/SNS) based on notification type.

**Key Orchestrations**:
- Loads email templates for each notification type
- Sends email via `AWSSESAdapter`
- Sends SMS via `TwilioSMSAdapter` (fallback: `AWSSNSAdapter`)
- All notifications are fire-and-forget (async background tasks in FastAPI)
- Logs send success/failure to CloudWatch

**Dependencies**:
- `AWSSESAdapter`, `TwilioSMSAdapter`, `AWSSNSAdapter`
- `IUserRepository` (to resolve phone/email from user_id)

---

### AdminApplicationService

**Purpose**: Aggregation service for admin dashboard and reporting features.

**Key Orchestrations**:
- Dashboard: query recent orders, revenue totals, low-stock products → compose DashboardDTO
- Sales report: aggregate orders by date range → group by product/category → compute totals
- Customer management: delegates to `IUserRepository` and `IOrderRepository`

**Dependencies**:
- `IOrderRepository`, `IProductRepository`, `IUserRepository`, `IPaymentRepository`

---

## 2. Cross-Cutting Services (FastAPI Middleware)

| Service | Type | Responsibility |
|---|---|---|
| `JWTAuthMiddleware` | FastAPI Middleware | Validates Bearer token on every protected request; injects `current_user` into request state |
| `AdminAuthGuard` | FastAPI Dependency | Raises 403 if `current_user.role != ADMIN` |
| `RateLimitMiddleware` | FastAPI Middleware | Rate limits auth endpoints (login: 10 req/min, register: 5 req/min) via Redis sliding window |
| `RequestLoggingMiddleware` | FastAPI Middleware | Structured request/response logging to CloudWatch (request_id, method, path, status, latency) |
| `GlobalExceptionHandler` | FastAPI Exception Handler | Catches unhandled exceptions, logs full trace to CloudWatch, returns generic 500 to client |
| `CORSMiddleware` | FastAPI Middleware | Restricts origins to allowed frontend domains only |
| `SecurityHeadersMiddleware` | FastAPI Middleware | Injects HTTP security headers on all responses (HSTS, CSP, X-Frame-Options, etc.) |

---

## 3. Frontend Services (API Client Layer)

| Service | Purpose |
|---|---|
| `apiClient` | Axios instance with base URL, auth token injection, 401 refresh token interceptor |
| `authService` | Wraps all `/api/v1/auth/*` calls |
| `productService` | Wraps all `/api/v1/products/*` and `/api/v1/categories/*` calls |
| `cartService` | Wraps all `/api/v1/cart/*` calls |
| `wishlistService` | Wraps all `/api/v1/wishlist/*` calls |
| `orderService` | Wraps all `/api/v1/orders/*` calls |
| `paymentService` | Wraps Razorpay widget initialization + `/api/v1/payments/*` calls |
| `addressService` | Wraps all `/api/v1/addresses/*` calls |
| `reviewService` | Wraps all `/api/v1/reviews/*` calls |
| `adminService` | Wraps all `/api/v1/admin/*` calls |
| `mediaService` | Calls `/api/v1/media/presigned-url` then uploads directly to S3 presigned URL |
