# Component Dependency Map
# Sabhyakriti — Saree eCommerce Website

---

## 1. System-Level Dependency Overview

```
+-----------------------------+        +-----------------------------+
|  sabhyakriti-frontend       |        |  sabhyakriti-backend        |
|  React + Redux Toolkit      |  REST  |  FastAPI (DDD)              |
|  Tailwind + shadcn/ui       |------->|  Python 3.11+               |
|  Separate Repository        |  JSON  |  Separate Repository        |
+-----------------------------+        +---+-------------------------+
                                           |
              +----------------------------+----------------------------+
              |                            |                            |
              v                            v                            v
   +----------+-------+        +----------+--------+        +----------+-------+
   |  PostgreSQL       |        |  AWS Services      |        |  External APIs   |
   |  AWS RDS          |        |  S3, SES, SNS,     |        |  Razorpay        |
   |  Primary + Read   |        |  CloudWatch,        |        |  Google OAuth    |
   |  Replica          |        |  CloudFront         |        |  Facebook OAuth  |
   +------------------+        +-------------------+         |  Twilio SMS      |
                                                              +------------------+
```

---

## 2. Backend Layer Dependencies

```
Presentation Layer (FastAPI Routers)
    |  depends on
    v
Application Layer (Application Services)
    |  depends on
    +---> Domain Layer (Entities + Domain Services + Repository Interfaces)
    |         (Domain layer has ZERO external dependencies)
    |
    +---> Infrastructure Layer (Repository Implementations + Adapters)
              |  depends on
              +---> PostgreSQL via SQLAlchemy
              +---> AWS SDK (boto3): S3, SES, SNS, CloudWatch
              +---> Razorpay Python SDK
              +---> Authlib: Google + Facebook OAuth
              +---> Twilio Python SDK
```

**Dependency Rule**: Inner layers never import from outer layers. Domain layer is fully isolated.

---

## 3. Application Service Dependencies

| Application Service | Depends On (Domain Services) | Depends On (Repositories) | Depends On (Adapters) | Calls (Other App Services) |
|---|---|---|---|---|
| `AuthApplicationService` | — | `IUserRepository` | `GoogleOAuthAdapter`, `FacebookOAuthAdapter`, `TwilioSMSAdapter`, `AWSSESAdapter` | `NotificationApplicationService` |
| `ProductApplicationService` | — | `IProductRepository`, `ICategoryRepository` | `AWSS3Adapter`, `AWSCloudFrontAdapter` | — |
| `CategoryApplicationService` | — | `ICategoryRepository`, `IProductRepository` | — | — |
| `CartApplicationService` | `PricingDomainService`, `InventoryDomainService` | `ICartRepository`, `IProductRepository`, `ICouponRepository` | — | — |
| `WishlistApplicationService` | — | `IWishlistRepository`, `IProductRepository` | — | — |
| `OrderApplicationService` | `OrderDomainService`, `InventoryDomainService` | `IOrderRepository`, `ICartRepository`, `IProductRepository`, `IAddressRepository` | — | `NotificationApplicationService` |
| `PaymentApplicationService` | — | `IPaymentRepository`, `IOrderRepository` | `RazorpayAdapter` | `NotificationApplicationService` |
| `ReviewApplicationService` | — | `IReviewRepository`, `IOrderRepository`, `IProductRepository` | — | — |
| `AddressApplicationService` | — | `IAddressRepository` | — | — |
| `NotificationApplicationService` | — | `IUserRepository` | `AWSSESAdapter`, `TwilioSMSAdapter`, `AWSSNSAdapter` | — |
| `AdminApplicationService` | — | `IOrderRepository`, `IProductRepository`, `IUserRepository`, `IPaymentRepository` | — | — |

---

## 4. Frontend Component Dependencies

### Page → Component Dependencies

| Page | Child Components Used |
|---|---|
| `PLPPage` | `PLPFilters`, `PLPSearch`, `PLPSort`, `ProductGrid` → `ProductCard`, `PLPPagination` |
| `PDPPage` | `ImageGallery` → `ImageLightbox`, `ProductAttributes`, `SizeGuide`, `StockIndicator`, `ReviewList`, `ReviewForm`, `RelatedProducts`, `Breadcrumb` |
| `CartPage` | `CartItem` (×n), `CartSummary`, `CouponInput`, `MiniCart` |
| `CheckoutPage` | `AddressStep` → `AddressForm`, `PaymentStep`, `OrderReviewStep` |
| `OrderDetailPage` | `OrderStatusTimeline`, `OrderPollingProvider`, `CancelOrderModal`, `ReturnRequestModal`, `InvoiceDownloadButton` |
| `AccountPage` | `ProfileForm`, `AddressBook` → `AddressForm`, `OrderHistoryPage`, `WishlistPage` |
| `AdminDashboard` | KPI cards, recent orders table |
| `ProductManager` | `ProductForm`, `BulkUploadPage` |

### Redux Slice → Component Consumer Map

| Redux Slice | Consumed By |
|---|---|
| `authSlice` | `LoginPage`, `RegisterPage`, `Header`, `ProtectedRoute`, `AdminRoute`, all pages |
| `cartSlice` | `CartPage`, `CartItem`, `CartSummary`, `MiniCart`, `CouponInput`, `CheckoutPage` |
| `productSlice` | `PLPPage`, `PLPFilters`, `PLPSearch`, `PLPSort`, `PLPPagination`, `ProductGrid` |
| `orderSlice` | `OrderHistoryPage`, `OrderDetailPage`, `OrderPollingProvider`, `OrderConfirmationPage` |
| `wishlistSlice` | `WishlistPage`, `WishlistItem`, `ProductCard` (wishlist icon state) |
| `uiSlice` | `ToastProvider`, modal consumers across all pages |

### Frontend → Backend API Dependencies

| Frontend Service | Backend Router Called |
|---|---|
| `authService` | `AuthRouter` (`/api/v1/auth/*`) |
| `productService` | `ProductRouter` + `CategoryRouter` |
| `cartService` | `CartRouter` |
| `wishlistService` | `WishlistRouter` |
| `orderService` | `OrderRouter` |
| `paymentService` | `PaymentRouter` + Razorpay JS SDK (direct to Razorpay) |
| `reviewService` | `ReviewRouter` |
| `addressService` | `AddressRouter` |
| `mediaService` | `MediaRouter` + direct S3 presigned URL upload |
| `adminService` | `AdminRouter` |

---

## 5. Data Flow: Critical Paths

### PLP Browse Flow
```
User navigates to /sarees
    → PLPPage renders
    → productService.listProducts(filters) dispatched
    → GET /api/v1/products?fabric=silk&page=1
    → ProductApplicationService.list_products
    → SQLAlchemyProductRepository (read replica)
    → Response → productSlice updated → ProductGrid re-renders
```

### Checkout + Payment Flow
```
User clicks "Place Order"
    → orderService.createOrder(address_id, payment_method=RAZORPAY)
    → POST /api/v1/orders
    → OrderApplicationService.create_order
        → InventoryDomainService.reserve_stock (atomic DB tx)
        → Order persisted (status=PENDING)
        → Cart cleared
    → paymentService.createRazorpayOrder(order_id)
    → POST /api/v1/payments/create-order
    → PaymentApplicationService.create_razorpay_order
        → RazorpayAdapter.create_order(amount)
        → Payment record persisted (status=CREATED)
        → Return razorpay_order_id to frontend
    → Razorpay JS widget opens (in browser)
    → User completes payment on Razorpay
    → Razorpay returns payment_id + signature to frontend
    → paymentService.verifyPayment(order_id, payment_id, signature)
    → POST /api/v1/payments/verify
    → PaymentApplicationService.verify_payment
        → RazorpayAdapter.verify_signature (HMAC-SHA256)
        → Payment status → CAPTURED
        → Order status → CONFIRMED
        → NotificationApplicationService.send_order_confirmation (async)
    → Frontend → OrderConfirmationPage
```

### Image Upload Flow
```
Admin selects image in ProductForm
    → mediaService.getPresignedUrl(product_id, 'jpg')
    → GET /api/v1/media/presigned-url
    → AWSS3Adapter.generate_presigned_upload_url(s3_key)
    → Returns presigned_url + s3_key to frontend
    → Frontend PUT directly to S3 presigned URL (no backend traffic)
    → Frontend calls mediaService.confirmUpload(product_id, s3_key, is_primary)
    → POST /api/v1/products/:id/images/confirm
    → ProductApplicationService.confirm_image_upload
        → AWSCloudFrontAdapter.build_cdn_url(s3_key)
        → ProductImage persisted with cloudfront_url
```

---

## 6. Dependency Boundaries — Critical Rules

| Rule | Description |
|---|---|
| Domain isolation | Domain layer entities and domain services have NO imports from infrastructure or application layers |
| Repository inversion | Application services depend on `IRepository` interfaces only; SQLAlchemy implementations injected at startup |
| Auth boundary | JWT validation and user context injection happen in `JWTAuthMiddleware` — application services receive already-validated `current_user` |
| Payment isolation | All Razorpay calls go exclusively through `PaymentApplicationService` and `RazorpayAdapter` — no other service calls Razorpay directly |
| Notification async | `NotificationApplicationService` calls are always dispatched as FastAPI background tasks — never block the main request path |
| Admin isolation | All `/api/v1/admin/*` routes are protected by both `JWTAuthMiddleware` and `AdminAuthGuard` |
| Frontend auth | `ProtectedRoute` HOC wraps all customer routes; `AdminRoute` HOC wraps all `/admin/*` routes |
| S3 direct upload | Product images upload directly from browser to S3 via presigned URL — backend never handles binary image data in the request body |
