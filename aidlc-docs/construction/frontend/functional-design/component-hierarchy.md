# Component Hierarchy & Page Map — Unit 9: Frontend

---

## Brand Theme
- Primary: Saffron `#FF6B2B`
- Secondary: Deep Teal `#1B4B5A`
- Background: `#FAFAFA`
- Text: `#1A1A1A`
- Font: Inter (sans-serif)

---

## Route Map

| Route | Component | Auth | Description |
|---|---|---|---|
| `/` | `HomePage` | Public | Hero + featured + categories + new arrivals |
| `/sarees` | `PLPPage` | Public | Product listing with filters/search/sort |
| `/sarees/:slug` | `PDPPage` | Public | Product detail with zoom gallery |
| `/login` | `LoginPage` | Public | Email/password + Google + Facebook + OTP |
| `/register` | `RegisterPage` | Public | Registration form |
| `/verify-email` | `VerifyEmailPage` | Public | Email verification landing |
| `/forgot-password` | `ForgotPasswordPage` | Public | Password reset request |
| `/reset-password` | `ResetPasswordPage` | Public | New password form |
| `/cart` | `CartPage` | Public | Cart with live totals + coupon |
| `/checkout` | `CheckoutPage` | Protected | 3-step: Address → Payment → Review |
| `/order-confirmation/:id` | `OrderConfirmationPage` | Protected | Post-order success |
| `/orders` | `OrderHistoryPage` | Protected | Paginated order list |
| `/orders/:id` | `OrderDetailPage` | Protected | Order detail + timeline + actions |
| `/account` | `AccountPage` | Protected | Profile + addresses + wishlist tabs |
| `/admin` | `AdminDashboard` | Admin | KPI dashboard |
| `/admin/products` | `ProductManager` | Admin | Product CRUD table |
| `/admin/products/new` | `ProductForm` | Admin | Add product |
| `/admin/products/:id/edit` | `ProductForm` | Admin | Edit product |
| `/admin/categories` | `CategoryManager` | Admin | Category CRUD |
| `/admin/orders` | `AdminOrderManager` | Admin | All orders with filters |
| `/admin/orders/:id` | `AdminOrderDetail` | Admin | Order detail + status update |
| `/admin/returns` | `ReturnManager` | Admin | Return requests |
| `/admin/customers` | `CustomerManager` | Admin | Customer list |
| `/admin/customers/:id` | `CustomerDetail` | Admin | Customer + order history |
| `/admin/coupons` | `CouponManager` | Admin | Coupon CRUD |
| `/admin/inventory` | `InventoryManager` | Admin | Stock update table |
| `/admin/reports` | `SalesReport` | Admin | Revenue charts + tables |
| `/admin/bulk-import` | `BulkImportPage` | Admin | CSV upload |

---

## Key Component Tree

```
App
├── AppLayout (Header + Footer)
│   ├── Header (Logo + Search + CartIcon + UserMenu)
│   │   ├── MiniCart (dropdown preview)
│   │   └── UserMenu (profile links / login CTA)
│   ├── CategoryNav (mega-menu: Fabric / Occasion / Region)
│   └── Footer (links + newsletter)
│
├── HomePage
│   ├── HeroBanner (full-width image + CTA)
│   ├── CategoryShortcuts (3 grid tiles: Fabric / Occasion / Region)
│   ├── FeaturedProducts (carousel of ProductCard ×8)
│   └── NewArrivals (grid of ProductCard ×8)
│
├── PLPPage
│   ├── PLPFilters (sidebar: Fabric checkboxes / Occasion / Region)
│   ├── PLPToolbar (product count + PLPSearch + PLPSort)
│   ├── ProductGrid → ProductCard ×n
│   └── PLPPagination
│
├── PDPPage
│   ├── Breadcrumb
│   ├── ImageGallery
│   │   ├── ThumbnailStrip
│   │   ├── MainImage (with react-image-magnify zoom on hover desktop)
│   │   └── ImageLightbox (full-screen modal + swipe on mobile)
│   ├── ProductInfo (name, price, discount, StockBadge)
│   ├── ProductAttributes (fabric, color, blouse, care)
│   ├── SizeGuideModal
│   ├── AddToCartSection (qty stepper + AddToCart + BuyNow + WishlistBtn)
│   ├── ReviewSection
│   │   ├── ReviewSummary (avg rating + breakdown)
│   │   ├── ReviewList → ReviewCard ×n
│   │   └── ReviewForm (authenticated)
│   └── RelatedProducts (horizontal scroll)
│
├── CartPage
│   ├── CartItemList → CartItem ×n
│   ├── CouponInput
│   └── CartSummary (subtotal + GST + shipping + total + CheckoutBtn)
│
├── CheckoutPage (stepper wizard)
│   ├── AddressStep (AddressSelector + AddressForm)
│   ├── PaymentStep (RazorpayButton / UPIButton / CODOption)
│   └── OrderReviewStep (summary + PlaceOrderBtn)
│
├── AdminLayout (Sidebar + AdminHeader)
│   └── [all admin pages]
```

---

## Redux Store Slices

| Slice | Key State | Key Actions |
|---|---|---|
| `authSlice` | user, tokens, isAuthenticated, loading | login, logout, setUser |
| `cartSlice` | items, totals, couponCode, loading | addItem, removeItem, updateQty, applyCoupon |
| `productSlice` | products, filters, search, sort, page, total, loading | setFilters, setSearch, setSort, setPage |
| `orderSlice` | orders, currentOrder, loading | setOrders, setCurrentOrder |
| `wishlistSlice` | items (product IDs set) | addToWishlist, removeFromWishlist |
| `uiSlice` | toast, lightboxOpen, lightboxImage | showToast, openLightbox |
