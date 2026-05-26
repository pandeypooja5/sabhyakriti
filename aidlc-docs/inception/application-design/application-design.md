# Application Design — Consolidated
# Sabhyakriti — Saree eCommerce Website

---

## 1. Architecture Summary

| Dimension | Decision |
|---|---|
| **Frontend** | React 18 + Tailwind CSS + shadcn/ui + Redux Toolkit |
| **State Management** | Redux Toolkit (authSlice, cartSlice, productSlice, orderSlice, wishlistSlice, uiSlice) |
| **Backend** | Python 3.11 + FastAPI — Domain-Driven Design (DDD) |
| **Database** | PostgreSQL 15 on AWS RDS (primary + read replica) |
| **Repository Structure** | Two separate repositories: `sabhyakriti-frontend` and `sabhyakriti-backend` |
| **Admin Panel** | Integrated in same React app — `/admin/*` routes guarded by `AdminRoute` HOC |
| **Image Upload** | Frontend → S3 presigned URL (direct upload) → CloudFront CDN serving |
| **Order Status Updates** | Polling: `OrderPollingProvider` polls `/api/v1/orders/:id` every 30 seconds |
| **Payment** | Razorpay (card/net banking/wallet/UPI) + COD |
| **Deployment** | AWS: EC2 Auto Scaling + ALB + RDS + S3 + CloudFront + SES + SNS + CloudWatch |

---

## 2. Backend DDD Layer Structure

```
sabhyakriti-backend/
|
+-- domain/                         # Zero external dependencies
|   +-- entities/                   # User, Product, Order, Payment, Cart, ...
|   +-- value_objects/              # OrderStatus, PaymentStatus, Money, ...
|   +-- services/                   # PricingDomainService, OrderDomainService, InventoryDomainService
|   +-- repositories/               # IUserRepository, IProductRepository, ... (interfaces/ports)
|
+-- application/                    # Orchestrates use cases
|   +-- services/                   # AuthAppService, ProductAppService, OrderAppService, ...
|   +-- dtos/                       # Request + Response data transfer objects
|   +-- commands/                   # Command objects (CreateOrderCmd, etc.)
|   +-- queries/                    # Query objects (ProductListQuery, etc.)
|
+-- infrastructure/                 # External concerns
|   +-- persistence/                # SQLAlchemy models + SQLAlchemy*Repository implementations
|   +-- adapters/                   # RazorpayAdapter, GoogleOAuthAdapter, AWSS3Adapter, AWSSESAdapter, ...
|   +-- database.py                 # SQLAlchemy engine + session factory
|
+-- presentation/                   # FastAPI layer
    +-- routers/                    # AuthRouter, ProductRouter, OrderRouter, AdminRouter, ...
    +-- middleware/                 # JWTAuthMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware, ...
    +-- dependencies.py             # FastAPI dependency injection (get_db, get_current_user, etc.)
    +-- main.py                     # FastAPI app setup, middleware registration, router inclusion
```

---

## 3. Frontend Structure

```
sabhyakriti-frontend/
|
+-- src/
    +-- pages/                      # Route-level page components
    |   +-- auth/                   # LoginPage, RegisterPage, OTPVerifyPage, ...
    |   +-- catalog/                # PLPPage
    |   +-- product/                # PDPPage
    |   +-- cart/                   # CartPage
    |   +-- checkout/               # CheckoutPage, OrderConfirmationPage
    |   +-- orders/                 # OrderHistoryPage, OrderDetailPage
    |   +-- account/                # AccountPage
    |   +-- admin/                  # AdminDashboard, ProductManager, OrderManager, ...
    |
    +-- components/                 # Reusable UI components
    |   +-- product/                # ProductCard, PLPFilters, ImageGallery, ImageLightbox, ...
    |   +-- cart/                   # CartItem, CartSummary, MiniCart, CouponInput
    |   +-- order/                  # OrderStatusTimeline, CancelOrderModal, ReturnRequestModal
    |   +-- shared/                 # Header, Footer, Breadcrumb, ProtectedRoute, AdminRoute, SEOHead
    |
    +-- store/                      # Redux store
    |   +-- slices/                 # authSlice, cartSlice, productSlice, orderSlice, wishlistSlice, uiSlice
    |   +-- store.ts                # Redux store configuration
    |
    +-- services/                   # API client wrappers
    |   +-- api/                    # apiClient (Axios), authService, productService, orderService, ...
    |
    +-- hooks/                      # Custom React hooks (useAuth, useCart, useWishlist, ...)
    +-- lib/                        # Utility functions (formatCurrency, formatDate, ...)
    +-- types/                      # TypeScript type definitions
    +-- App.tsx                     # Root component + React Router setup
    +-- main.tsx                    # Entry point
```

---

## 4. Domain Entities Quick Reference

| Entity | Key Fields | Relationships |
|---|---|---|
| `User` | user_id, email, phone, role, is_verified | has one Cart, Wishlist; has many Orders, Addresses, Reviews |
| `Product` | product_id, name, price, discount_price, stock_qty, is_active | has many ProductImages, ProductCategories, Reviews; referenced by CartItems, OrderItems, WishlistItems |
| `Category` | category_id, name, type (FABRIC/OCCASION/REGION), slug | many-to-many with Product |
| `Order` | order_id, status, total_amount, address_snapshot | belongs to User; has many OrderItems, one Payment |
| `OrderItem` | order_item_id, quantity, unit_price (price snapshot) | belongs to Order and Product |
| `Payment` | payment_id, razorpay_order_id, razorpay_payment_id, status, method | belongs to Order (one-to-one) |
| `Cart` | cart_id, applied_coupon_code | belongs to User (one-to-one); has many CartItems |
| `Address` | address_id, full_name, phone, full address, is_default | belongs to User |
| `Review` | review_id, rating, title, body, is_verified_purchase | belongs to User and Product |
| `Coupon` | coupon_id, code, type, value, min_order, max_uses, used_count, expiry | applied on Cart |

---

## 5. API Design Conventions

- **Base URL**: `/api/v1/`
- **Auth**: Bearer JWT in `Authorization` header on all protected routes
- **Admin routes**: `/api/v1/admin/*` — require ADMIN role
- **Pagination**: `?page=1&page_size=24` on list endpoints
- **Filtering**: Query params on product list (`?fabric=silk&occasion=bridal&region=banarasi`)
- **Errors**: Standard JSON error response `{ "detail": "...", "code": "..." }`
- **Versioning**: URL path versioning (`/v1/`, `/v2/` when breaking changes needed)
- **Docs**: FastAPI auto-generates OpenAPI spec at `/docs` and `/redoc` (disabled in production)

---

## 6. Security Design Summary (aligned with SECURITY-01 to SECURITY-15)

| Security Concern | Design Decision |
|---|---|
| Passwords | Argon2id hashing via `passlib` |
| JWT | Access token 15 min TTL; refresh token 7 days; stored in httpOnly cookie or secure local storage |
| OAuth | PKCE flow for Google/Facebook; state param CSRF protection |
| OTP | 6-digit OTP, Argon2id-hashed in DB, 5-minute TTL, max 3 attempts |
| Payment signature | Razorpay HMAC-SHA256 signature verified server-side before payment capture |
| Rate limiting | Redis-based sliding window: 10 req/min login, 5 req/min register, 3 req/min OTP |
| CORS | Explicit allow-list of frontend domains only |
| HTTP headers | SecurityHeadersMiddleware: HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy |
| Admin access | Separate MFA-required login; `AdminAuthGuard` on all admin routes |
| Input validation | Pydantic v2 schemas on all request bodies; strict type checking |
| Audit logging | Critical operations (order status change, payment, refund, admin actions) logged to CloudWatch |
| S3 access | Bucket is private; all access via presigned URLs or CloudFront signed URLs |

---

## 7. Design Artifacts Index

| Artifact | File | Contents |
|---|---|---|
| Component Definitions | `components.md` | All frontend and backend components with responsibilities |
| Component Methods | `component-methods.md` | Method signatures for all application services and domain services |
| Services | `services.md` | Service orchestration patterns and cross-cutting middleware |
| Component Dependencies | `component-dependency.md` | Dependency matrix, data flow diagrams, critical path flows |
| This document | `application-design.md` | Consolidated architecture summary |
