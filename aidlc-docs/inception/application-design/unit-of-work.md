# Units of Work
# Sabhyakriti — Saree eCommerce Website

---

## Architecture & Decomposition Decisions

| Decision | Choice | Rationale |
|---|---|---|
| **Backend model** | Microservices | Each domain deployed as an independent FastAPI service |
| **Unit scope** | Backend-first | Units 1–7 = backend services; Unit 8 = infrastructure; Unit 9 = React frontend |
| **Development model** | Solo sequential | All units built one at a time by a single developer |
| **MVP scope** | All 9 units | Full platform (including Admin Panel) before launch |
| **Database strategy** | Shared PostgreSQL, separate schemas | One RDS instance, each service owns its schema — practical for solo development |
| **Inter-service communication** | Synchronous HTTP (REST) | Services call each other via internal ALB/API Gateway; no message queue for MVP |
| **Container strategy** | Docker on EC2 | Each microservice runs as a Docker container; deployed via GitHub Actions CI/CD |
| **Auth strategy** | Distributed JWT validation | Each service validates Bearer JWT independently using shared public key |

---

## Unit Overview

| # | Unit Name | Type | Repository |
|---|---|---|---|
| 1 | Auth Microservice | Backend (FastAPI) | `sabhyakriti-auth-service` |
| 2 | Product Microservice | Backend (FastAPI) | `sabhyakriti-product-service` |
| 3 | Cart & Wishlist Microservice | Backend (FastAPI) | `sabhyakriti-cart-service` |
| 4 | Order Microservice | Backend (FastAPI) | `sabhyakriti-order-service` |
| 5 | Payment Microservice | Backend (FastAPI) | `sabhyakriti-payment-service` |
| 6 | Notification Microservice | Backend (FastAPI) | `sabhyakriti-notification-service` |
| 7 | Admin Microservice | Backend (FastAPI) | `sabhyakriti-admin-service` |
| 8 | AWS Infrastructure | IaC (AWS CDK / Python) | `sabhyakriti-infra` |
| 9 | Frontend | React Application | `sabhyakriti-frontend` |

---

## Unit 1: Auth Microservice

**Repository**: `sabhyakriti-auth-service`
**Deployment**: Docker container on EC2, port 8001

**Responsibilities**:
- User registration with email + password
- Email verification on registration
- Login: email/password, Google OAuth, Facebook OAuth, Phone OTP
- JWT access token issuance (RS256, 15 min TTL)
- Refresh token management (stored in Redis, 7 day TTL)
- Password reset flow (email link)
- User profile read/update
- Token introspection endpoint (used by other services for JWT validation)
- MFA enforcement for admin accounts

**Domain Entities owned**: `User`, `RefreshToken`, `OTPRecord`, `PasswordResetToken`

**Database schema**: `auth` schema in shared PostgreSQL

**External dependencies**: Google OAuth API, Facebook Graph API, Twilio SMS API, AWS SES, Redis

**API base path**: `/api/v1/auth`, `/api/v1/users`

**Code structure**:
```
sabhyakriti-auth-service/
+-- domain/
|   +-- entities/          # User, RefreshToken, OTPRecord
|   +-- value_objects/     # UserRole, OAuthProvider
|   +-- services/          # (no domain services — auth is primarily application logic)
|   +-- repositories/      # IUserRepository, ITokenRepository
+-- application/
|   +-- services/          # AuthApplicationService
|   +-- dtos/              # RegisterDTO, LoginDTO, TokenPairDTO, UserProfileDTO
|   +-- commands/
+-- infrastructure/
|   +-- persistence/       # SQLAlchemyUserRepository, SQLAlchemyTokenRepository
|   +-- adapters/          # GoogleOAuthAdapter, FacebookOAuthAdapter, TwilioSMSAdapter, AWSSESAdapter
|   +-- cache/             # RedisTokenStore
+-- presentation/
|   +-- routers/           # auth_router.py, users_router.py
|   +-- middleware/        # RateLimitMiddleware, SecurityHeadersMiddleware, LoggingMiddleware
+-- main.py
+-- Dockerfile
+-- requirements.txt / pyproject.toml
+-- alembic/               # DB migrations for auth schema
```

---

## Unit 2: Product Microservice

**Repository**: `sabhyakriti-product-service`
**Deployment**: Docker container on EC2, port 8002

**Responsibilities**:
- Product CRUD (admin operations)
- Category CRUD — Fabric, Occasion, Region types (admin)
- Product listing with multi-filter (fabric, occasion, region), search (full-text), sort, pagination
- Product detail fetch (single product with images, categories, average rating)
- Related products fetch (same category)
- Product image management — generate S3 presigned upload URL, confirm image upload
- Stock quantity tracking (read only — stock reservation done by Order Service)
- Bulk product import via CSV (admin)
- Product review CRUD (customer submit, admin/customer delete)

**Domain Entities owned**: `Product`, `Category`, `ProductCategory`, `ProductImage`, `Review`

**Database schema**: `product` schema in shared PostgreSQL

**External dependencies**: AWS S3, AWS CloudFront

**API base path**: `/api/v1/products`, `/api/v1/categories`, `/api/v1/reviews`, `/api/v1/media`

**Code structure**:
```
sabhyakriti-product-service/
+-- domain/
|   +-- entities/          # Product, Category, ProductImage, Review
|   +-- value_objects/     # CategoryType, Money
|   +-- repositories/      # IProductRepository, ICategoryRepository, IReviewRepository
+-- application/
|   +-- services/          # ProductApplicationService, CategoryApplicationService, ReviewApplicationService
|   +-- dtos/
+-- infrastructure/
|   +-- persistence/
|   +-- adapters/          # AWSS3Adapter, AWSCloudFrontAdapter
+-- presentation/
|   +-- routers/           # products_router.py, categories_router.py, reviews_router.py, media_router.py
|   +-- middleware/
+-- main.py
+-- Dockerfile
+-- requirements.txt
+-- alembic/
```

---

## Unit 3: Cart & Wishlist Microservice

**Repository**: `sabhyakriti-cart-service`
**Deployment**: Docker container on EC2, port 8003

**Responsibilities**:
- Cart CRUD per authenticated user (persisted in DB)
- Add, update quantity, remove cart items
- Cart totals calculation (subtotal, discount, taxes, shipping)
- Coupon/discount code validation and application
- Wishlist CRUD per authenticated user
- Internal endpoint for Order Service to read and clear cart at checkout

**Domain Entities owned**: `Cart`, `CartItem`, `Wishlist`, `WishlistItem`, `Coupon`

**Database schema**: `cart` schema in shared PostgreSQL

**External dependencies**: Product Microservice (fetch current product prices + availability)

**API base path**: `/api/v1/cart`, `/api/v1/wishlist`, `/api/v1/coupons` (admin)

**Code structure**:
```
sabhyakriti-cart-service/
+-- domain/
|   +-- entities/          # Cart, CartItem, Wishlist, WishlistItem, Coupon
|   +-- value_objects/     # CouponType, Money
|   +-- services/          # PricingDomainService
|   +-- repositories/      # ICartRepository, IWishlistRepository, ICouponRepository
+-- application/
|   +-- services/          # CartApplicationService, WishlistApplicationService
|   +-- clients/           # ProductServiceClient (HTTP)
+-- infrastructure/
+-- presentation/
|   +-- routers/           # cart_router.py, wishlist_router.py, coupon_router.py
+-- main.py
+-- Dockerfile
```

---

## Unit 4: Order Microservice

**Repository**: `sabhyakriti-order-service`
**Deployment**: Docker container on EC2, port 8004

**Responsibilities**:
- Create order from cart (snapshot prices, reserve stock)
- Full order lifecycle management: PENDING → CONFIRMED → SHIPPED → DELIVERED
- Customer: view order history, order detail, cancel order, submit return request
- Admin: view all orders, update order status, add tracking number, manage return requests
- Stock reservation and release (coordinates with Product Service)
- Invoice PDF generation per order
- Trigger notifications on status changes (calls Notification Service)

**Domain Entities owned**: `Order`, `OrderItem`, `Address`, `ReturnRequest`

**Database schema**: `order` schema in shared PostgreSQL

**External dependencies**: Cart Microservice (read cart), Product Microservice (reserve/release stock), Notification Microservice (trigger emails/SMS), Auth Microservice (user info)

**API base path**: `/api/v1/orders`, `/api/v1/addresses`

**Code structure**:
```
sabhyakriti-order-service/
+-- domain/
|   +-- entities/          # Order, OrderItem, Address, ReturnRequest
|   +-- value_objects/     # OrderStatus, Money
|   +-- services/          # OrderDomainService, InventoryDomainService
|   +-- repositories/      # IOrderRepository, IAddressRepository
+-- application/
|   +-- services/          # OrderApplicationService, AddressApplicationService
|   +-- clients/           # CartServiceClient, ProductServiceClient, NotificationServiceClient
+-- infrastructure/
+-- presentation/
|   +-- routers/           # orders_router.py, addresses_router.py
+-- main.py
+-- Dockerfile
```

---

## Unit 5: Payment Microservice

**Repository**: `sabhyakriti-payment-service`
**Deployment**: Docker container on EC2, port 8005

**Responsibilities**:
- Create Razorpay order object for frontend widget initialization
- Verify Razorpay payment signature after frontend payment completion
- Handle Razorpay webhooks (payment.captured, refund.created, payment.failed)
- COD order confirmation (no payment needed — notifies Order Service directly)
- Admin-triggered refund initiation via Razorpay Refund API
- Payment receipt generation and storage

**Domain Entities owned**: `Payment`

**Database schema**: `payment` schema in shared PostgreSQL

**External dependencies**: Razorpay API, Order Microservice (update order status), Notification Microservice (payment/refund confirmations)

**API base path**: `/api/v1/payments`

**Code structure**:
```
sabhyakriti-payment-service/
+-- domain/
|   +-- entities/          # Payment
|   +-- value_objects/     # PaymentStatus, PaymentMethod
|   +-- repositories/      # IPaymentRepository
+-- application/
|   +-- services/          # PaymentApplicationService
|   +-- clients/           # OrderServiceClient, NotificationServiceClient
+-- infrastructure/
|   +-- adapters/          # RazorpayAdapter
+-- presentation/
|   +-- routers/           # payments_router.py
+-- main.py
+-- Dockerfile
```

---

## Unit 6: Notification Microservice

**Repository**: `sabhyakriti-notification-service`
**Deployment**: Docker container on EC2, port 8006

**Responsibilities**:
- Send all transactional emails via AWS SES (order confirmation, shipped, delivered, cancelled, refunded, password reset, email verification)
- Send all SMS notifications via Twilio (OTP, order shipped, order delivered)
- Fallback SMS via AWS SNS if Twilio unavailable
- All send operations are async (background tasks) — callers fire-and-forget
- Email template rendering (Jinja2 HTML templates)
- Notification send log (success/failure tracking in CloudWatch)

**Domain Entities owned**: `NotificationLog` (send audit only)

**Database schema**: `notification` schema (minimal — logs only)

**External dependencies**: AWS SES, AWS SNS, Twilio SMS API, Auth Microservice (resolve user contact info)

**API base path**: `/internal/v1/notifications` (internal only — not exposed via API Gateway)

**Code structure**:
```
sabhyakriti-notification-service/
+-- domain/
+-- application/
|   +-- services/          # NotificationApplicationService
|   +-- templates/         # Jinja2 HTML email templates
+-- infrastructure/
|   +-- adapters/          # AWSSESAdapter, AWSSNSAdapter, TwilioSMSAdapter
+-- presentation/
|   +-- routers/           # notifications_router.py (internal)
+-- main.py
+-- Dockerfile
```

---

## Unit 7: Admin Microservice

**Repository**: `sabhyakriti-admin-service`
**Deployment**: Docker container on EC2, port 8007

**Responsibilities**:
- Admin dashboard: revenue KPIs, order counts, low-stock alerts (aggregates from other services)
- Sales reports: revenue by date range, top products, category performance
- Customer management: list customers, view customer order history
- Coupon lifecycle management (delegates to Cart Service for coupon CRUD)
- Admin-level product actions (bulk import coordination with Product Service)
- Admin-level order actions (delegates to Order Service)
- Admin-level return/refund actions (delegates to Order + Payment Services)

**Note**: Admin Microservice is primarily an aggregation/BFF (Backend-for-Frontend) layer for the admin panel. Core business operations are delegated to the respective domain services.

**Domain Entities owned**: None (reads/writes via other services)

**Database schema**: No own schema — reads from other service schemas via internal APIs

**External dependencies**: Auth, Product, Cart, Order, Payment Microservices

**API base path**: `/api/v1/admin`

**Code structure**:
```
sabhyakriti-admin-service/
+-- application/
|   +-- services/          # AdminApplicationService (aggregation)
|   +-- clients/           # ProductServiceClient, OrderServiceClient, PaymentServiceClient, AuthServiceClient
+-- presentation/
|   +-- routers/           # admin_router.py (products, orders, customers, reports, coupons sub-routers)
+-- main.py
+-- Dockerfile
```

---

## Unit 8: AWS Infrastructure

**Repository**: `sabhyakriti-infra`
**Tooling**: AWS CDK (Python)

**Responsibilities**:
- VPC with public and private subnets across 2 AZs
- Security groups (ALB, EC2, RDS, ElastiCache)
- Application Load Balancer (ALB) with HTTPS listener and ACM certificate
- API Gateway routing rules (path-based routing to each microservice)
- EC2 instances (one per microservice) in private subnet with Auto Scaling
- AWS RDS PostgreSQL 15 (primary + read replica) in private subnet
- AWS ElastiCache Redis (for JWT refresh tokens, OTP store, rate limiting)
- AWS S3 bucket (product images) with public access blocked
- AWS CloudFront distribution (S3 origin + ALB origin)
- AWS SES configuration (sending domain verification, DKIM)
- AWS SNS topic (SMS fallback)
- AWS CloudWatch: log groups per service, dashboards, alarms
- AWS IAM roles and least-privilege policies per service
- GitHub Actions CI/CD pipelines per service (build → push Docker image → deploy to EC2)
- Route 53 DNS records (sabhyakriti.com, api.sabhyakriti.com, admin.sabhyakriti.com)

**Code structure**:
```
sabhyakriti-infra/
+-- sabhyakriti_infra/
|   +-- stacks/
|       +-- network_stack.py       # VPC, subnets, security groups
|       +-- compute_stack.py       # EC2 + ALB + Auto Scaling
|       +-- database_stack.py      # RDS + ElastiCache
|       +-- storage_stack.py       # S3 + CloudFront
|       +-- messaging_stack.py     # SES + SNS
|       +-- monitoring_stack.py    # CloudWatch alarms + dashboards
|       +-- iam_stack.py           # IAM roles + policies
+-- app.py
+-- requirements.txt
```

---

## Unit 9: Frontend

**Repository**: `sabhyakriti-frontend`
**Tooling**: React 18 + Vite + TypeScript + Tailwind CSS + shadcn/ui + Redux Toolkit

**Responsibilities**:
- All customer-facing pages: Auth (login/register/OTP/OAuth), PLP (browse, filter, search), PDP (details, gallery, reviews), Cart, Checkout, Order History, Account, Wishlist
- Admin panel pages (integrated, `/admin/*` routes): Dashboard, Product Manager, Category Manager, Order Manager, Customer Manager, Inventory Manager, Coupon Manager, Reports, Bulk Upload
- API Gateway integration (all HTTP calls via `apiClient` Axios instance)
- Razorpay JS SDK integration for payment widget
- SEO: React Helmet for dynamic meta tags per page
- Responsive design (mobile-first)

**Note**: Frontend is built after all backend microservices (Units 1–7) are complete, so the API contracts are stable before frontend implementation begins.

**Code structure**: As defined in `application-design.md` Section 3.

---

## Development Sequence (Solo Developer)

```
Unit 1 (Auth)          → Unit 2 (Products)     → Unit 3 (Cart)
    → Unit 4 (Orders)  → Unit 5 (Payments)     → Unit 6 (Notifications)
    → Unit 7 (Admin)   → Unit 8 (Infrastructure) → Unit 9 (Frontend)
```

Each unit is fully designed, implemented, and tested before moving to the next.
Unit 8 (Infrastructure) IaC is written last and codifies the deployment of all 7 backend services simultaneously.
