import apiClient from './apiClient';
import { normalizeOrder } from './orderService';
import type {
  DashboardKPIs,
  SalesReport,
  User,
  Order,
  ReturnRequest,
  Coupon,
  Product,
  PaginatedResponse,
  OrderStatus,
} from '@/types';

export const getDashboard = async (): Promise<{ kpis: DashboardKPIs; recentOrders: Order[] }> => {
  const res = await apiClient.get('/admin/dashboard');
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const d = res.data as any;
  const kpis: DashboardKPIs = {
    totalRevenue: Number(d.revenue_30d ?? d.totalRevenue ?? 0),
    totalOrders: Number(d.orders_30d ?? d.totalOrders ?? 0),
    totalCustomers: Number(d.new_customers_30d ?? d.totalCustomers ?? 0),
    totalProducts: Number(d.low_stock_products ?? d.totalProducts ?? 0),
    averageOrderValue: Number(d.average_order_value ?? d.averageOrderValue ?? 0),
    pendingReturns: Number(d.pending_returns ?? d.pendingReturns ?? 0),
    revenueGrowth: Number(d.revenue_growth ?? d.revenueGrowth ?? 0),
    orderGrowth: Number(d.order_growth ?? d.orderGrowth ?? 0),
  };
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recentOrders: Order[] = (d.recent_orders ?? d.recentOrders ?? []).map((o: any) => {
    const order = normalizeOrder(o);
    // Prefer customer_name from summary if shipping_address is missing
    if (!order.shippingAddress.name && o.customer_name) {
      order.shippingAddress = { ...order.shippingAddress, name: o.customer_name };
    }
    return order;
  });
  return { kpis, recentOrders };
};

export const getSalesReport = async (from: string, to: string): Promise<SalesReport> => {
  const res = await apiClient.get('/admin/reports/sales', { params: { from, to } });
  return res.data;
};

// ─── Customers ────────────────────────────────────────────────────────────────

export const listCustomers = async (page = 1, search?: string): Promise<PaginatedResponse<User>> => {
  const res = await apiClient.get('/admin/customers', { params: { page, search } });
  return res.data;
};

export const getCustomerDetail = async (id: string): Promise<{ user: User; orders: Order[] }> => {
  const res = await apiClient.get(`/admin/customers/${id}`);
  return res.data;
};

// ─── Orders ───────────────────────────────────────────────────────────────────

export const listAllOrders = async (
  page = 1,
  status?: string,
  search?: string
): Promise<PaginatedResponse<Order>> => {
  const res = await apiClient.get('/admin/orders', { params: { page, status, search } });
  const d = res.data ?? {};
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const items = (d.items ?? d.data ?? []) as any[];
  return {
    data: items.map(normalizeOrder),
    total: Number(d.total ?? items.length),
    page: Number(d.page ?? page),
    pageSize: Number(d.page_size ?? d.pageSize ?? 20),
    totalPages: Number(d.total_pages ?? d.totalPages ?? 1),
  };
};

export const getAdminOrderDetail = async (orderId: string): Promise<Order> => {
  const res = await apiClient.get(`/admin/orders/${orderId}`);
  return normalizeOrder(res.data.order ?? res.data);
};

export const updateOrderStatus = async (
  orderId: string,
  status: OrderStatus,
  trackingNumber?: string,
  courierName?: string
): Promise<Order> => {
  const res = await apiClient.patch(`/admin/orders/${orderId}/status`, {
    new_status: status,
    tracking_number: trackingNumber,
    courier_name: courierName,
  });
  return normalizeOrder(res.data.order ?? res.data);
};

// ─── Returns ──────────────────────────────────────────────────────────────────

export const listReturns = async (status?: string): Promise<PaginatedResponse<ReturnRequest>> => {
  const res = await apiClient.get('/admin/returns', { params: { status } });
  return res.data;
};

export const processReturn = async (
  returnId: string,
  action: 'APPROVE' | 'REJECT',
  adminNote?: string
): Promise<ReturnRequest> => {
  const res = await apiClient.patch(`/admin/returns/${returnId}`, { action, adminNote });
  return res.data.returnRequest ?? res.data;
};

export const initiateRefund = async (returnId: string, amount: number): Promise<{ refundId: string }> => {
  const res = await apiClient.post(`/admin/returns/${returnId}/refund`, { amount });
  return res.data;
};

// ─── Coupons ──────────────────────────────────────────────────────────────────

export const listCoupons = async (): Promise<Coupon[]> => {
  const res = await apiClient.get('/admin/coupons');
  return res.data.coupons ?? res.data;
};

export const createCoupon = async (data: Omit<Coupon, 'id' | 'usedCount' | 'createdAt'>): Promise<Coupon> => {
  const res = await apiClient.post('/admin/coupons', data);
  return res.data.coupon ?? res.data;
};

export const updateCoupon = async (id: string, data: Partial<Coupon>): Promise<Coupon> => {
  const res = await apiClient.patch(`/admin/coupons/${id}`, data);
  return res.data.coupon ?? res.data;
};

export const deleteCoupon = async (id: string): Promise<void> => {
  await apiClient.delete(`/admin/coupons/${id}`);
};

// ─── Inventory ────────────────────────────────────────────────────────────────

export const listInventory = async (page = 1): Promise<PaginatedResponse<Product>> => {
  const res = await apiClient.get('/admin/inventory', { params: { page } });
  return res.data;
};

export const updateStock = async (productId: string, quantity: number): Promise<Product> => {
  const res = await apiClient.patch(`/admin/inventory/${productId}`, { stockQuantity: quantity });
  return res.data.product ?? res.data;
};
