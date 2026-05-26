# Component Definitions
# Sabhyakriti — Saree eCommerce Website

Architecture: React (Tailwind + shadcn/ui + Redux Toolkit) — FastAPI (DDD) — PostgreSQL — AWS

---

## 1. FRONTEND COMPONENTS (sabhyakriti-frontend)

### 1.1 Auth Domain

| Component | Type | Responsibilities |
|---|---|---|
| `LoginPage` | Page | Email/password login form, Google OAuth button, Facebook OAuth button, Phone OTP link |
| `RegisterPage` | Page | Registration form with email/password; triggers email verification |
| `OTPVerifyPage` | Page | Phone number entry, OTP input, verify OTP action |
| `OAuthCallbackPage` | Page | Handles redirect from Google/Facebook after OAuth; exchanges code for session |
| `ForgotPasswordPage` | Page | Email input to trigger password reset link |
| `ResetPasswordPage` | Page | New password form, validates reset token from URL |

### 1.2 Product Catalog / PLP Domain

| Component | Type | Responsibilities |
|---|---|---|
| `PLPPage` | Page | Orchestrates PLP layout — assembles filters, search bar, sort, product grid |
| `ProductGrid` | UI | Renders paginated grid of ProductCard components |
| `ProductCard` | UI | Displays product thumbnail, name, price, discount; "Add to Wishlist" icon |
| `PLPFilters` | UI | Collapsible sidebar with three filter dimensions: Fabric, Occasion, Region; multi-select |
| `PLPSearch` | UI | Debounced search input; dispatches search query to Redux productSlice |
| `PLPSort` | UI | Dropdown to select sort order (price asc/desc, newest, popularity) |
| `PLPPagination` | UI | Page controls; syncs with Redux productSlice pagination state |

### 1.3 Product Detail / PDP Domain

| Component | Type | Responsibilities |
|---|---|---|
| `PDPPage` | Page | Orchestrates PDP layout — assembles gallery, details panel, reviews, related products |
| `ImageGallery` | UI | Thumbnail strip + main image display; click thumbnail to switch main image |
| `ImageLightbox` | UI | Full-screen modal with zoom on click from ImageGallery; keyboard navigation (left/right) |
| `ProductAttributes` | UI | Displays fabric, color, pattern, blouse included, dimensions, care instructions |
| `SizeGuide` | UI | Modal/drawer showing size reference chart |
| `StockIndicator` | UI | Badge showing In Stock / Low Stock / Out of Stock |
| `ReviewList` | UI | Paginated list of customer reviews with star ratings |
| `ReviewForm` | UI | Authenticated form to submit star rating + review text |
| `RelatedProducts` | UI | Horizontal carousel of related ProductCard components |
| `Breadcrumb` | UI | Home > Category > Sub-category > Product Name navigation |

### 1.4 Cart Domain

| Component | Type | Responsibilities |
|---|---|---|
| `CartPage` | Page | Full cart view with all CartItem rows, CartSummary, CouponInput, proceed-to-checkout CTA |
| `CartItem` | UI | Single cart row: image, name, price, quantity stepper, remove button |
| `CartSummary` | UI | Subtotal, applied discount, estimated shipping, taxes, total; live-updated via Redux |
| `CouponInput` | UI | Coupon code field with apply/remove; dispatches to Redux cartSlice |
| `MiniCart` | UI | Header dropdown preview of cart items and total; link to CartPage |

### 1.5 Wishlist Domain

| Component | Type | Responsibilities |
|---|---|---|
| `WishlistPage` | Page | Grid of saved WishlistItem cards with "Add to Cart" and "Remove" actions |
| `WishlistItem` | UI | ProductCard variant with wishlist-specific actions |

### 1.6 Checkout Domain

| Component | Type | Responsibilities |
|---|---|---|
| `CheckoutPage` | Page | Multi-step checkout wizard: Address → Payment → Review |
| `AddressStep` | UI | Select saved address or add new; dispatches to checkoutSlice |
| `AddressForm` | UI | Form for new delivery address (name, phone, street, city, state, pincode) |
| `PaymentStep` | UI | Razorpay widget trigger, UPI option, COD option selector |
| `OrderReviewStep` | UI | Summary of items, address, payment method before final "Place Order" |
| `OrderConfirmationPage` | Page | Post-order success page with order ID, summary, estimated delivery |

### 1.7 Order Management Domain

| Component | Type | Responsibilities |
|---|---|---|
| `OrderHistoryPage` | Page | Paginated list of past orders with status badge, date, total |
| `OrderDetailPage` | Page | Full order detail: items, address, payment method, timeline, tracking link |
| `OrderStatusTimeline` | UI | Visual stepper showing order lifecycle stages |
| `OrderPollingProvider` | UI | Background polling component (30s interval) for active order status updates |
| `CancelOrderModal` | UI | Confirmation modal with cancellation reason selector |
| `ReturnRequestModal` | UI | Form to select items and reason for return/refund |
| `InvoiceDownloadButton` | UI | Triggers PDF invoice download for a completed order |

### 1.8 User Account Domain

| Component | Type | Responsibilities |
|---|---|---|
| `AccountPage` | Page | Tab layout: Profile / Address Book / Order History / Wishlist |
| `ProfileForm` | UI | Edit name, email, phone; change password section |
| `AddressBook` | UI | List of saved addresses with default designation, edit, delete |

### 1.9 Admin Domain

| Component | Type | Responsibilities |
|---|---|---|
| `AdminLayout` | Layout | Admin sidebar navigation, admin header; wraps all `/admin/*` pages |
| `AdminDashboard` | Page | KPI cards (revenue, orders, stock alerts), recent orders table |
| `ProductManager` | Page | Product CRUD table with search, filters; link to ProductForm |
| `ProductForm` | UI | Add/edit product form: all attributes + S3 presigned image upload |
| `CategoryManager` | Page | CRUD for Fabric, Occasion, Region categories |
| `InventoryManager` | Page | Stock quantity update table with low-stock threshold configuration |
| `OrderManager` | Page | All orders table with status filter, status update action, tracking number input |
| `CustomerManager` | Page | Customer list with order history drill-down |
| `ReturnManager` | Page | Pending return requests; approve/reject with refund initiation |
| `CouponManager` | Page | CRUD for discount codes with expiry, type (flat/percent), usage limits |
| `SalesReportPage` | Page | Revenue charts, top-product table, category performance by date range |
| `BulkUploadPage` | Page | CSV upload for batch product creation with validation feedback |

### 1.10 Shared / Layout

| Component | Type | Responsibilities |
|---|---|---|
| `AppLayout` | Layout | Header, Footer, Navbar wrapping all customer-facing pages |
| `Header` | UI | Logo, search bar, cart icon (with count badge), wishlist icon, user menu |
| `Footer` | UI | Links, contact info, social media icons, newsletter signup |
| `Navbar` | UI | Category navigation mega-menu |
| `ProtectedRoute` | HOC | Redirects unauthenticated users to `/login` |
| `AdminRoute` | HOC | Redirects non-admin users to home page |
| `ToastProvider` | Context | Global toast notifications (success/error/info) |
| `SEOHead` | Utility | Sets page title, meta description, OG tags per page |

### 1.11 Redux Store Slices

| Slice | State Managed |
|---|---|
| `authSlice` | Current user, JWT tokens, auth loading state |
| `cartSlice` | Cart items, quantities, applied coupon, cart totals |
| `productSlice` | Product list, active filters, search query, sort order, pagination |
| `orderSlice` | Order history list, current order detail, polling active flag |
| `wishlistSlice` | Wishlist item IDs, full wishlist items |
| `uiSlice` | Global loading flags, modal open states |

---

## 2. BACKEND COMPONENTS (sabhyakriti-backend — DDD)

### 2.1 Domain Layer

#### Entities

| Entity | Core Identity | Key Attributes |
|---|---|---|
| `User` | user_id (UUID) | email, phone, hashed_password, role (CUSTOMER/ADMIN), is_verified, oauth_provider |
| `Product` | product_id (UUID) | name, description, price, discount_price, stock_qty, sku, is_active |
| `Category` | category_id (UUID) | name, type (FABRIC/OCCASION/REGION), slug, parent_id (nullable) |
| `ProductCategory` | product_id + category_id | Many-to-many join between Product and Category |
| `ProductImage` | image_id (UUID) | product_id, s3_key, cloudfront_url, is_primary, sort_order |
| `Order` | order_id (UUID) | user_id, status (OrderStatus enum), total_amount, shipping_address snapshot |
| `OrderItem` | order_item_id (UUID) | order_id, product_id, quantity, unit_price (snapshot at order time) |
| `Payment` | payment_id (UUID) | order_id, razorpay_order_id, razorpay_payment_id, status (PaymentStatus enum), amount, method |
| `Cart` | cart_id (UUID) | user_id (one-to-one), updated_at |
| `CartItem` | cart_item_id (UUID) | cart_id, product_id, quantity |
| `Wishlist` | wishlist_id (UUID) | user_id (one-to-one) |
| `WishlistItem` | wishlist_item_id (UUID) | wishlist_id, product_id |
| `Address` | address_id (UUID) | user_id, full_name, phone, address_line1, city, state, pincode, is_default |
| `Review` | review_id (UUID) | product_id, user_id, rating (1-5), title, body, is_verified_purchase |
| `Coupon` | coupon_id (UUID) | code, type (FLAT/PERCENT), value, min_order_amount, max_uses, used_count, expiry_date |

#### Value Objects

| Value Object | Description |
|---|---|
| `OrderStatus` | Enum: PENDING, CONFIRMED, SHIPPED, DELIVERED, CANCELLED, RETURN_REQUESTED, RETURNED, REFUNDED |
| `PaymentStatus` | Enum: CREATED, AUTHORIZED, CAPTURED, FAILED, REFUNDED |
| `UserRole` | Enum: CUSTOMER, ADMIN |
| `PaymentMethod` | Enum: RAZORPAY, UPI, COD |
| `Money` | Decimal amount + currency (INR), arithmetic operations, formatting |
| `CouponType` | Enum: FLAT_DISCOUNT, PERCENTAGE_DISCOUNT |

#### Domain Services

| Domain Service | Responsibilities |
|---|---|
| `PricingDomainService` | Calculates cart total, applies coupon discount, computes taxes (GST), validates coupon eligibility |
| `OrderDomainService` | Validates order creation preconditions (stock, address), enforces cancellation/return window rules |
| `InventoryDomainService` | Checks stock availability, reserves stock on order, releases on cancellation |

### 2.2 Application Layer (Use Cases)

See `services.md` for full application service definitions.

### 2.3 Infrastructure Layer

#### Repository Implementations (SQLAlchemy)

| Repository | Interface Implemented |
|---|---|
| `SQLAlchemyUserRepository` | `IUserRepository` |
| `SQLAlchemyProductRepository` | `IProductRepository` |
| `SQLAlchemyCategoryRepository` | `ICategoryRepository` |
| `SQLAlchemyOrderRepository` | `IOrderRepository` |
| `SQLAlchemyPaymentRepository` | `IPaymentRepository` |
| `SQLAlchemyCartRepository` | `ICartRepository` |
| `SQLAlchemyWishlistRepository` | `IWishlistRepository` |
| `SQLAlchemyAddressRepository` | `IAddressRepository` |
| `SQLAlchemyReviewRepository` | `IReviewRepository` |
| `SQLAlchemyCouponRepository` | `ICouponRepository` |

#### External Service Adapters

| Adapter | External System | Responsibility |
|---|---|---|
| `RazorpayAdapter` | Razorpay API | Create order, verify payment signature, initiate refund |
| `GoogleOAuthAdapter` | Google Identity | Exchange auth code for tokens, fetch user profile |
| `FacebookOAuthAdapter` | Facebook Graph API | Exchange auth code for tokens, fetch user profile |
| `TwilioSMSAdapter` | Twilio SMS API | Send OTP SMS, send order notification SMS |
| `AWSS3Adapter` | AWS S3 | Generate presigned upload URL, delete object, copy object |
| `AWSCloudFrontAdapter` | AWS CloudFront | Build CDN URL for an S3 object key |
| `AWSSESAdapter` | AWS SES | Send transactional emails (order confirmation, reset password, etc.) |
| `AWSSNSAdapter` | AWS SNS (fallback SMS) | Alternative SMS path for OTP and notifications |

### 2.4 Presentation Layer (FastAPI Routers)

| Router | Base Path | Handles |
|---|---|---|
| `AuthRouter` | `/api/v1/auth` | register, login, OAuth callback, OTP, refresh token, logout, password reset |
| `ProductRouter` | `/api/v1/products` | list (with filters/search/sort/page), get by ID/slug |
| `CategoryRouter` | `/api/v1/categories` | list all, list by type, get by ID |
| `CartRouter` | `/api/v1/cart` | get cart, add item, update quantity, remove item, apply/remove coupon |
| `WishlistRouter` | `/api/v1/wishlist` | get wishlist, add item, remove item |
| `OrderRouter` | `/api/v1/orders` | create order, list orders, get order detail, cancel order, return request |
| `PaymentRouter` | `/api/v1/payments` | create Razorpay order, verify payment, webhook, get receipt |
| `ReviewRouter` | `/api/v1/reviews` | list by product, submit review, delete own review |
| `AddressRouter` | `/api/v1/addresses` | list, add, update, delete, set default |
| `MediaRouter` | `/api/v1/media` | get presigned S3 upload URL |
| `UserRouter` | `/api/v1/users/me` | get profile, update profile |
| `AdminRouter` | `/api/v1/admin` | all admin sub-routes (products, categories, orders, customers, coupons, reports) |
