// ─── User & Auth ───────────────────────────────────────────────────────────────

export type UserRole = 'CUSTOMER' | 'ADMIN' | 'SUPER_ADMIN';

export interface User {
  id: string;
  email: string;
  name: string;
  phone?: string;
  role: UserRole;
  isVerified: boolean;
  avatar?: string;
  createdAt: string;
  updatedAt: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

// ─── Category ──────────────────────────────────────────────────────────────────

export type CategoryType = 'FABRIC' | 'OCCASION' | 'REGION';

export interface Category {
  id: string;
  name: string;
  slug: string;
  type: CategoryType;
  description?: string;
  imageUrl?: string;
  productCount?: number;
  createdAt: string;
  updatedAt: string;
}

// ─── Product ───────────────────────────────────────────────────────────────────

export interface ProductImage {
  id: string;
  url: string;
  altText?: string;
  isPrimary: boolean;
  sortOrder: number;
}

export type StockStatus = 'IN_STOCK' | 'LOW_STOCK' | 'OUT_OF_STOCK';

export interface Product {
  id: string;
  name: string;
  slug: string;
  sku: string;
  description: string;
  mrp: number;
  price: number;
  discountPercent: number;
  stockStatus: StockStatus;
  stockQuantity: number;
  images: ProductImage[];
  fabric?: string;
  color?: string;
  blouseIncluded: boolean;
  length?: number;
  blouseLength?: number;
  careInstructions?: string;
  material?: string;
  weaveType?: string;
  fabricCategories: Category[];
  occasionCategories: Category[];
  regionCategories: Category[];
  avgRating: number;
  reviewCount: number;
  isActive: boolean;
  isFeatured: boolean;
  createdAt: string;
  updatedAt: string;
}

// ─── Cart ──────────────────────────────────────────────────────────────────────

export interface CartItem {
  id: string;
  productId: string;
  product: Product;
  quantity: number;
  unitPrice: number;
  subtotal: number;
}

export interface CartTotals {
  subtotal: number;
  discountAmount: number;
  couponDiscount: number;
  gstAmount: number;
  shippingAmount: number;
  total: number;
  itemCount: number;
}

export interface Cart {
  id: string;
  items: CartItem[];
  totals: CartTotals;
  couponCode?: string;
  couponDiscount?: number;
}

// ─── Address ───────────────────────────────────────────────────────────────────

export interface Address {
  id: string;
  userId: string;
  name: string;
  phone: string;
  line1: string;
  line2?: string;
  city: string;
  state: string;
  pincode: string;
  country: string;
  isDefault: boolean;
  addressType: 'HOME' | 'WORK' | 'OTHER';
}

// ─── Order ─────────────────────────────────────────────────────────────────────

export type OrderStatus =
  | 'PENDING'
  | 'CONFIRMED'
  | 'PROCESSING'
  | 'SHIPPED'
  | 'OUT_FOR_DELIVERY'
  | 'DELIVERED'
  | 'CANCELLED'
  | 'RETURN_REQUESTED'
  | 'RETURNED'
  | 'REFUNDED';

export type PaymentMethod = 'RAZORPAY' | 'UPI' | 'COD';
export type PaymentStatus = 'PENDING' | 'PAID' | 'FAILED' | 'REFUNDED';

export interface OrderItem {
  id: string;
  productId: string;
  product: Product;
  quantity: number;
  unitPrice: number;
  subtotal: number;
  returnStatus?: 'NONE' | 'REQUESTED' | 'APPROVED' | 'REJECTED';
  returnReason?: string;
}

export interface OrderStatusHistory {
  status: OrderStatus;
  timestamp: string;
  note?: string;
}

export interface Order {
  id: string;
  orderNumber: string;
  userId: string;
  items: OrderItem[];
  shippingAddress: Address;
  paymentMethod: PaymentMethod;
  paymentStatus: PaymentStatus;
  razorpayOrderId?: string;
  razorpayPaymentId?: string;
  status: OrderStatus;
  statusHistory: OrderStatusHistory[];
  subtotal: number;
  discountAmount: number;
  couponDiscount: number;
  gstAmount: number;
  shippingAmount: number;
  total: number;
  couponCode?: string;
  trackingNumber?: string;
  courierName?: string;
  estimatedDelivery?: string;
  deliveredAt?: string;
  cancelReason?: string;
  createdAt: string;
  updatedAt: string;
}

// ─── Review ────────────────────────────────────────────────────────────────────

export interface Review {
  id: string;
  productId: string;
  userId: string;
  user: Pick<User, 'id' | 'name' | 'avatar'>;
  rating: number;
  title: string;
  body: string;
  isVerifiedPurchase: boolean;
  helpfulCount: number;
  createdAt: string;
  updatedAt: string;
}

// ─── Coupon ────────────────────────────────────────────────────────────────────

export type DiscountType = 'PERCENT' | 'FLAT';

export interface Coupon {
  id: string;
  code: string;
  description?: string;
  discountType: DiscountType;
  discountValue: number;
  minOrderValue?: number;
  maxDiscountAmount?: number;
  usageLimit?: number;
  usedCount: number;
  isActive: boolean;
  expiresAt?: string;
  createdAt: string;
}

// ─── Wishlist ──────────────────────────────────────────────────────────────────

export interface WishlistItem {
  id: string;
  productId: string;
  product: Product;
  addedAt: string;
}

// ─── Pagination ────────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// ─── Filters ───────────────────────────────────────────────────────────────────

export interface ProductFilters {
  fabricIds?: string[];
  occasionIds?: string[];
  regionIds?: string[];
  search?: string;
  minPrice?: number;
  maxPrice?: number;
  inStock?: boolean;
  sort?: 'newest' | 'price_asc' | 'price_desc' | 'rating' | 'popularity';
  page?: number;
  pageSize?: number;
}

// ─── Admin ─────────────────────────────────────────────────────────────────────

export interface DashboardKPIs {
  totalRevenue: number;
  totalOrders: number;
  totalCustomers: number;
  totalProducts: number;
  revenueGrowth: number;
  orderGrowth: number;
  averageOrderValue: number;
  pendingReturns: number;
}

export interface SalesDataPoint {
  date: string;
  revenue: number;
  orders: number;
}

export interface TopProduct {
  productId: string;
  name: string;
  revenue: number;
  unitsSold: number;
}

export interface SalesReport {
  period: { from: string; to: string };
  dataPoints: SalesDataPoint[];
  topProducts: TopProduct[];
  categoryBreakdown: { categoryName: string; revenue: number; percentage: number }[];
  totalRevenue: number;
  totalOrders: number;
}

// ─── Return ────────────────────────────────────────────────────────────────────

export type ReturnStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'COMPLETED';

export interface ReturnRequest {
  id: string;
  orderId: string;
  order: Order;
  items: { orderItemId: string; quantity: number; reason: string }[];
  status: ReturnStatus;
  adminNote?: string;
  refundAmount?: number;
  createdAt: string;
  updatedAt: string;
}

// ─── Payment ───────────────────────────────────────────────────────────────────

export interface RazorpayOrderResponse {
  razorpayOrderId: string;
  amount: number;
  currency: string;
  keyId: string;
}

export interface PaymentVerificationPayload {
  razorpayOrderId: string;
  razorpayPaymentId: string;
  razorpaySignature: string;
  orderId: string;
}
