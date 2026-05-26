# Code Summary — Unit 9: Frontend

117 files generated under `sabhyakriti-frontend/` (108 TypeScript/TSX + 9 config files).

## Tech Stack
React 18 + Vite 5 + TypeScript 5 + Tailwind CSS + shadcn/ui + Redux Toolkit + React Router v6 + Axios + Razorpay JS SDK

## Architecture
- 6 Redux slices: auth (JWT persistence + refresh), cart, product (filters+URL sync), order, wishlist, ui
- Axios JWT interceptor with refresh token queue (no duplicate race conditions)
- All interactive elements have data-testid attributes

## Key Features
- **Homepage** (/): HeroBanner + CategoryShortcuts + FeaturedProducts + NewArrivals
- **PLP** (/sarees): 3-dimension checkbox filters (Fabric/Occasion/Region) synced to URL params, debounced search, 5 sort options, pagination
- **PDP** (/sarees/:slug): react-medium-image-zoom (click + pinch-to-zoom), lightbox, product attributes accordion, size guide modal, review form, related products
- **Cart**: Live totals with GST as separate line item, coupon input
- **Checkout**: 3-step wizard → Address → Payment (Razorpay/UPI/COD) → Review → Confirmation
- **Orders**: History + detail + 30s status polling + cancel modal + partial return modal + PDF invoice download
- **Admin Panel**: Dashboard KPIs + recharts BarChart/LineChart + product/category/order/customer/coupon/inventory/returns management
- **Razorpay**: loadRazorpay() dynamic script loader → widget → verifyPayment flow

## Brand
Saffron #FF6B2B + Deep Teal #1B4B5A, Inter font, light mode only

## Tests
5 test files: formatINR edge cases, phone/pincode validation, ProductCard render, CartSummary GST calculation, CouponInput apply/remove
