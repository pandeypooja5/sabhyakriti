# Component Methods
# Sabhyakriti — Saree eCommerce Website

Note: Detailed business logic and rules are defined in Functional Design (per-unit, CONSTRUCTION phase).
This document defines method signatures, inputs, outputs, and high-level purpose only.

---

## 1. BACKEND APPLICATION SERVICES

### AuthApplicationService

| Method | Input | Output | Purpose |
|---|---|---|---|
| `register_with_email` | `RegisterEmailCmd(email, password, full_name)` | `UserDTO` | Create account, hash password, send verification email |
| `login_with_email` | `LoginEmailCmd(email, password)` | `TokenPairDTO` | Validate credentials, issue JWT access + refresh tokens |
| `login_with_oauth` | `OAuthLoginCmd(provider, code, redirect_uri)` | `TokenPairDTO` | Exchange OAuth code, create/link user, issue tokens |
| `send_phone_otp` | `SendOTPCmd(phone_number)` | `void` | Generate OTP, store hash, send via SMS adapter |
| `verify_phone_otp` | `VerifyOTPCmd(phone_number, otp_code)` | `TokenPairDTO` | Validate OTP, create/find user, issue tokens |
| `refresh_tokens` | `RefreshCmd(refresh_token)` | `TokenPairDTO` | Validate refresh token, issue new access token |
| `logout` | `LogoutCmd(user_id, refresh_token)` | `void` | Revoke refresh token server-side |
| `request_password_reset` | `PasswordResetRequestCmd(email)` | `void` | Generate reset token, send via email adapter |
| `reset_password` | `PasswordResetCmd(token, new_password)` | `void` | Validate token, hash and persist new password |
| `verify_email` | `VerifyEmailCmd(token)` | `void` | Mark user email as verified |

### ProductApplicationService

| Method | Input | Output | Purpose |
|---|---|---|---|
| `list_products` | `ProductListQuery(filters, search, sort, page, page_size)` | `PagedDTO[ProductSummaryDTO]` | Fetch paginated, filtered, sorted product list for PLP |
| `get_product_detail` | `ProductDetailQuery(product_id)` | `ProductDetailDTO` | Fetch full product details, images, categories for PDP |
| `get_product_by_slug` | `ProductSlugQuery(slug)` | `ProductDetailDTO` | SEO-friendly PDP URL resolution |
| `get_related_products` | `RelatedProductQuery(product_id, limit)` | `list[ProductSummaryDTO]` | Fetch products in same category |
| `create_product` | `CreateProductCmd(admin_id, product_data)` | `ProductDetailDTO` | Admin: create new product with attributes |
| `update_product` | `UpdateProductCmd(admin_id, product_id, update_data)` | `ProductDetailDTO` | Admin: update product fields |
| `delete_product` | `DeleteProductCmd(admin_id, product_id)` | `void` | Admin: soft-delete product |
| `update_stock` | `UpdateStockCmd(admin_id, product_id, quantity)` | `void` | Admin: set stock quantity |
| `bulk_import_products` | `BulkImportCmd(admin_id, csv_rows)` | `BulkImportResultDTO` | Admin: batch create/update products from CSV |
| `get_presigned_upload_url` | `PresignedUrlQuery(product_id, file_extension)` | `PresignedUrlDTO` | Generate S3 presigned URL for frontend image upload |
| `confirm_image_upload` | `ConfirmImageCmd(product_id, s3_key, is_primary)` | `ProductImageDTO` | Register S3 object as product image after frontend upload |

### CategoryApplicationService

| Method | Input | Output | Purpose |
|---|---|---|---|
| `list_categories` | `CategoryListQuery(type?)` | `list[CategoryDTO]` | List all or filtered-by-type categories |
| `create_category` | `CreateCategoryCmd(admin_id, name, type, parent_id?)` | `CategoryDTO` | Admin: create category |
| `update_category` | `UpdateCategoryCmd(admin_id, category_id, data)` | `CategoryDTO` | Admin: rename or re-parent category |
| `delete_category` | `DeleteCategoryCmd(admin_id, category_id)` | `void` | Admin: delete category if no active products use it |

### CartApplicationService

| Method | Input | Output | Purpose |
|---|---|---|---|
| `get_cart` | `CartQuery(user_id)` | `CartDTO` | Fetch cart with items and real-time pricing |
| `add_to_cart` | `AddToCartCmd(user_id, product_id, quantity)` | `CartDTO` | Add item or increment quantity; check stock |
| `update_cart_item` | `UpdateCartItemCmd(user_id, cart_item_id, quantity)` | `CartDTO` | Change item quantity; quantity=0 removes item |
| `remove_from_cart` | `RemoveCartItemCmd(user_id, cart_item_id)` | `CartDTO` | Remove single item from cart |
| `apply_coupon` | `ApplyCouponCmd(user_id, coupon_code)` | `CartDTO` | Validate and apply coupon; compute discount |
| `remove_coupon` | `RemoveCouponCmd(user_id)` | `CartDTO` | Remove applied coupon from cart |

### WishlistApplicationService

| Method | Input | Output | Purpose |
|---|---|---|---|
| `get_wishlist` | `WishlistQuery(user_id)` | `WishlistDTO` | Fetch all wishlist items with product details |
| `add_to_wishlist` | `AddToWishlistCmd(user_id, product_id)` | `void` | Add product to wishlist; idempotent |
| `remove_from_wishlist` | `RemoveFromWishlistCmd(user_id, product_id)` | `void` | Remove product from wishlist |

### OrderApplicationService

| Method | Input | Output | Purpose |
|---|---|---|---|
| `create_order` | `CreateOrderCmd(user_id, address_id, payment_method)` | `OrderDTO` | Convert cart to order, reserve stock, create payment record |
| `get_order_detail` | `OrderDetailQuery(user_id, order_id)` | `OrderDTO` | Fetch full order with items, payment, status timeline |
| `list_orders` | `OrderListQuery(user_id, page, page_size)` | `PagedDTO[OrderSummaryDTO]` | Paginated order history for customer |
| `cancel_order` | `CancelOrderCmd(user_id, order_id, reason)` | `OrderDTO` | Cancel order if within allowed window; release stock |
| `request_return` | `ReturnRequestCmd(user_id, order_id, items, reason)` | `ReturnRequestDTO` | Initiate return for delivered order |
| `update_order_status` | `UpdateStatusCmd(admin_id, order_id, status, tracking_no?)` | `OrderDTO` | Admin: advance order to next status |
| `get_all_orders` | `AdminOrderListQuery(filters, page, page_size)` | `PagedDTO[OrderSummaryDTO]` | Admin: list all orders with filters |
| `process_return` | `ProcessReturnCmd(admin_id, return_id, approve)` | `ReturnRequestDTO` | Admin: approve or reject return request |
| `generate_invoice` | `InvoiceQuery(user_id, order_id)` | `bytes (PDF)` | Generate PDF invoice for a completed order |

### PaymentApplicationService

| Method | Input | Output | Purpose |
|---|---|---|---|
| `create_razorpay_order` | `CreatePaymentOrderCmd(order_id, amount)` | `RazorpayOrderDTO` | Create Razorpay order object to initialize widget |
| `verify_payment` | `VerifyPaymentCmd(order_id, razorpay_payment_id, razorpay_signature)` | `PaymentDTO` | Verify Razorpay HMAC signature, capture payment, update order |
| `handle_webhook` | `WebhookCmd(payload, signature)` | `void` | Process Razorpay webhook events (payment.captured, refund.created, etc.) |
| `initiate_refund` | `InitiateRefundCmd(admin_id, order_id, amount?, reason)` | `RefundDTO` | Admin: call Razorpay refund API, update payment status |
| `get_payment_receipt` | `PaymentReceiptQuery(user_id, order_id)` | `PaymentReceiptDTO` | Fetch payment details for receipt display/email |

### ReviewApplicationService

| Method | Input | Output | Purpose |
|---|---|---|---|
| `list_product_reviews` | `ReviewListQuery(product_id, page, page_size)` | `PagedDTO[ReviewDTO]` | Paginated reviews for a product |
| `submit_review` | `SubmitReviewCmd(user_id, product_id, rating, title, body)` | `ReviewDTO` | Create review; validates verified purchase |
| `delete_review` | `DeleteReviewCmd(user_id, review_id)` | `void` | Customer deletes own review; admin can delete any |

### AddressApplicationService

| Method | Input | Output | Purpose |
|---|---|---|---|
| `list_addresses` | `AddressListQuery(user_id)` | `list[AddressDTO]` | Fetch all saved addresses for user |
| `add_address` | `AddAddressCmd(user_id, address_data)` | `AddressDTO` | Create and optionally set as default |
| `update_address` | `UpdateAddressCmd(user_id, address_id, data)` | `AddressDTO` | Update address fields |
| `delete_address` | `DeleteAddressCmd(user_id, address_id)` | `void` | Remove address; reassign default if needed |
| `set_default_address` | `SetDefaultCmd(user_id, address_id)` | `void` | Mark address as default; clear previous default |

### NotificationApplicationService

| Method | Input | Output | Purpose |
|---|---|---|---|
| `send_order_confirmation` | `OrderConfirmNotif(user_id, order_id)` | `void` | Send order placed email + SMS to customer |
| `send_order_shipped` | `ShippedNotif(user_id, order_id, tracking_no)` | `void` | Send shipped email + SMS with tracking link |
| `send_order_delivered` | `DeliveredNotif(user_id, order_id)` | `void` | Send delivered email + SMS |
| `send_order_cancelled` | `CancelledNotif(user_id, order_id)` | `void` | Send cancellation email |
| `send_refund_processed` | `RefundNotif(user_id, order_id, amount)` | `void` | Send refund confirmation email |
| `send_password_reset` | `PasswordResetNotif(user_id, reset_link)` | `void` | Send password reset email |
| `send_otp` | `OTPNotif(phone_number, otp_code)` | `void` | Send OTP SMS via Twilio/SNS |

### AdminApplicationService

| Method | Input | Output | Purpose |
|---|---|---|---|
| `get_dashboard_summary` | `DashboardQuery(admin_id, date_range)` | `DashboardDTO` | Revenue KPIs, order counts, low-stock alerts |
| `get_sales_report` | `SalesReportQuery(admin_id, from_date, to_date)` | `SalesReportDTO` | Revenue by date, top products, category breakdown |
| `list_customers` | `CustomerListQuery(admin_id, filters, page)` | `PagedDTO[CustomerSummaryDTO]` | Admin customer list |
| `get_customer_detail` | `CustomerDetailQuery(admin_id, user_id)` | `CustomerDetailDTO` | Customer profile + order history |
| `manage_coupon` | `CouponCmd(admin_id, operation, coupon_data)` | `CouponDTO` | Create/update/deactivate coupon |

---

## 2. DOMAIN SERVICE METHODS

### PricingDomainService

| Method | Input | Output | Purpose |
|---|---|---|---|
| `calculate_cart_total` | `Cart, list[Product], Coupon?` | `CartTotalsVO` | Subtotal, discount, GST, final total |
| `validate_coupon` | `Coupon, Cart, User` | `CouponValidationResult` | Check code valid, not expired, usage limit, min order met |
| `apply_coupon_discount` | `Money, Coupon` | `Money` | Compute discounted amount (flat or percent) |

### OrderDomainService

| Method | Input | Output | Purpose |
|---|---|---|---|
| `validate_order_creation` | `Cart, Address, list[Product]` | `OrderValidationResult` | Check all items in stock, address valid, cart non-empty |
| `can_cancel` | `Order` | `bool` | True if order status allows cancellation (PENDING or CONFIRMED) |
| `can_return` | `Order` | `bool` | True if within return window after delivery |

### InventoryDomainService

| Method | Input | Output | Purpose |
|---|---|---|---|
| `check_availability` | `product_id, quantity` | `bool` | True if stock >= requested quantity |
| `reserve_stock` | `list[(product_id, quantity)]` | `void` | Decrement stock for all order items atomically |
| `release_stock` | `list[(product_id, quantity)]` | `void` | Increment stock on cancellation/return |

---

## 3. FRONTEND KEY HOOKS / REDUX THUNKS

| Hook / Thunk | Purpose |
|---|---|
| `useAuth()` | Access current user, login/logout actions |
| `useCart()` | Cart state, add/remove/update dispatchers |
| `useWishlist()` | Wishlist state, add/remove dispatchers |
| `fetchProducts(filters)` | Async thunk: GET /api/v1/products |
| `fetchProductDetail(id)` | Async thunk: GET /api/v1/products/:id |
| `placeOrder(addressId, paymentMethod)` | Async thunk: POST /api/v1/orders |
| `pollOrderStatus(orderId)` | Interval-based thunk: GET /api/v1/orders/:id every 30s |
| `verifyRazorpayPayment(payload)` | Async thunk: POST /api/v1/payments/verify |
