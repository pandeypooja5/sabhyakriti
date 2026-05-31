import apiClient from './apiClient';
import type { Order, Address, PaginatedResponse, Cart } from '@/types';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function normalizeOrder(raw: any): Order {
  const r = raw ?? {};
  const addr = r.shipping_address ?? r.shippingAddress ?? {};
  const gst = Number(r.cgst_amount ?? 0) + Number(r.sgst_amount ?? 0);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const items = (r.items ?? []) as any[];
  return {
    id: String(r.order_id ?? r.id ?? ''),
    orderNumber: String(r.order_number ?? r.orderNumber ?? ''),
    userId: String(r.user_id ?? ''),
    items: items.map((it) => {
      const img = it.product_image_url ?? it.productImage ?? '';
      return {
        id: String(it.order_item_id ?? it.id ?? ''),
        productId: String(it.product_id ?? ''),
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        product: {
          id: String(it.product_id ?? ''),
          name: String(it.product_name ?? ''),
          slug: '',
          sku: '',
          description: '',
          price: Number(it.discounted_price ?? it.unit_price ?? 0),
          mrp: Number(it.unit_price ?? 0),
          discountPercent: 0,
          stockStatus: 'IN_STOCK',
          stockQuantity: 0,
          images: img ? [{ url: img, isPrimary: true, altText: '', id: '', sortOrder: 0 }] : [],
          fabric: '',
          blouseIncluded: false,
          careInstructions: '',
          fabricCategories: [],
          occasionCategories: [],
          regionCategories: [],
          avgRating: 0,
          reviewCount: 0,
          isActive: true,
          isFeatured: false,
          createdAt: '',
          updatedAt: '',
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
        } as any,
        quantity: Number(it.quantity ?? 0),
        unitPrice: Number(it.discounted_price ?? it.unit_price ?? 0),
        subtotal: Number(it.line_total ?? 0),
      };
    }),
    shippingAddress: {
      id: String(addr.address_id ?? addr.id ?? ''),
      userId: String(addr.user_id ?? ''),
      name: String(addr.full_name ?? addr.name ?? ''),
      phone: String(addr.phone ?? ''),
      line1: String(addr.address_line1 ?? addr.line1 ?? ''),
      line2: String(addr.address_line2 ?? addr.line2 ?? ''),
      city: String(addr.city ?? ''),
      state: String(addr.state ?? ''),
      pincode: String(addr.pincode ?? ''),
      country: String(addr.country ?? 'India'),
      isDefault: Boolean(addr.is_default ?? false),
      addressType: 'HOME',
    } as Address,
    paymentMethod: r.payment_method ?? r.paymentMethod ?? 'COD',
    paymentStatus: (r.payment_status ?? r.paymentStatus ?? 'PENDING'),
    status: r.status ?? 'PENDING',
    statusHistory: [],
    subtotal: Number(r.subtotal ?? 0),
    discountAmount: Number(r.discount_amount ?? 0),
    couponDiscount: Number(r.discount_amount ?? 0),
    gstAmount: gst,
    shippingAmount: Number(r.shipping_charge ?? 0),
    total: Number(r.total_amount ?? r.total ?? 0),
    couponCode: r.coupon_code ?? undefined,
    cancelReason: r.cancellation_reason ?? undefined,
    deliveredAt: r.delivered_at ?? undefined,
    createdAt: r.created_at ?? r.createdAt ?? '',
    updatedAt: r.updated_at ?? r.updatedAt ?? '',
  } as Order;
}

function normalizeAddress(raw: Record<string, unknown>): Address {
  return {
    id: String(raw.address_id ?? raw.id ?? ''),
    userId: String(raw.user_id ?? ''),
    name: String(raw.full_name ?? raw.name ?? ''),
    phone: String(raw.phone ?? ''),
    line1: String(raw.address_line1 ?? raw.line1 ?? ''),
    line2: String(raw.address_line2 ?? raw.line2 ?? ''),
    city: String(raw.city ?? ''),
    state: String(raw.state ?? ''),
    pincode: String(raw.pincode ?? ''),
    country: String(raw.country ?? 'India'),
    isDefault: Boolean(raw.is_default ?? raw.isDefault ?? false),
    addressType: String(raw.address_type ?? raw.addressType ?? 'HOME') as Address['addressType'],
  };
}

export const createOrder = async (data: {
  addressId: string;
  paymentMethod: string;
  couponCode?: string;
  cart: Cart;
}): Promise<Order> => {
  const { cart } = data;
  const gst = Number(cart.totals.gstAmount ?? 0);
  const payload = {
    address_id: data.addressId,
    payment_method: data.paymentMethod,
    notes: null,
    cart_data: {
      cart_id: cart.id || '00000000-0000-0000-0000-000000000000',
      items: cart.items.map((item) => ({
        product_id: item.productId,
        variant_id: null,
        product_name: item.product?.name ?? 'Product',
        product_image_url:
          item.product?.images?.[0]?.url ?? 'https://via.placeholder.com/300',
        unit_price: item.unitPrice,
        discounted_price: item.unitPrice,
        quantity: item.quantity,
        hsn_code: '5208',
      })),
      subtotal: cart.totals.subtotal,
      discount_amount: cart.totals.discountAmount ?? 0,
      shipping_charge: cart.totals.shippingAmount ?? 0,
      cgst_amount: Number((gst / 2).toFixed(2)),
      sgst_amount: Number((gst / 2).toFixed(2)),
      total_amount: cart.totals.total,
      coupon_code: data.couponCode ?? null,
    },
  };
  const res = await apiClient.post('/orders', payload);
  return normalizeOrder(res.data.order ?? res.data);
};

export const listOrders = async (page = 1, pageSize = 10): Promise<PaginatedResponse<Order>> => {
  const res = await apiClient.get('/orders', { params: { page, pageSize } });
  const d = res.data ?? {};
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const items = (d.items ?? d.data ?? []) as any[];
  return {
    data: items.map(normalizeOrder),
    total: Number(d.total ?? items.length),
    page: Number(d.page ?? page),
    pageSize: Number(d.page_size ?? d.pageSize ?? pageSize),
    totalPages: Number(d.total_pages ?? d.totalPages ?? 1),
  };
};

export const getOrderDetail = async (orderId: string): Promise<Order> => {
  const res = await apiClient.get(`/orders/${orderId}`);
  return normalizeOrder(res.data.order ?? res.data);
};

export const cancelOrder = async (orderId: string, reason: string): Promise<Order> => {
  const res = await apiClient.post(`/orders/${orderId}/cancel`, { reason });
  return res.data.order ?? res.data;
};

export const submitReturn = async (data: {
  orderId: string;
  items: { orderItemId: string; quantity: number; reason: string }[];
}): Promise<{ returnRequestId: string }> => {
  const res = await apiClient.post(`/orders/${data.orderId}/return`, { items: data.items });
  return res.data;
};

export const downloadInvoice = async (orderId: string): Promise<Blob> => {
  const res = await apiClient.get(`/orders/${orderId}/invoice`, { responseType: 'blob' });
  return res.data;
};

// ─── Addresses ────────────────────────────────────────────────────────────────

export const listAddresses = async (): Promise<Address[]> => {
  const res = await apiClient.get('/addresses');
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const addresses = (res.data.addresses ?? res.data ?? []) as any[];
  return addresses.map(normalizeAddress);
};

export const addAddress = async (data: Omit<Address, 'id' | 'userId'>): Promise<Address> => {
  const payload = {
    full_name: data.name,
    phone: data.phone,
    address_line1: data.line1,
    address_line2: data.line2,
    city: data.city,
    state: data.state,
    pincode: data.pincode,
  };
  const res = await apiClient.post('/addresses', payload);
  return normalizeAddress(res.data.address ?? res.data);
};

export const updateAddress = async (id: string, data: Partial<Address>): Promise<Address> => {
  const payload: Record<string, unknown> = {};
  if (data.name) payload.full_name = data.name;
  if (data.phone) payload.phone = data.phone;
  if (data.line1) payload.address_line1 = data.line1;
  if (data.line2) payload.address_line2 = data.line2;
  if (data.city) payload.city = data.city;
  if (data.state) payload.state = data.state;
  if (data.pincode) payload.pincode = data.pincode;
  const res = await apiClient.patch(`/addresses/${id}`, payload);
  return normalizeAddress(res.data.address ?? res.data);
};

export const deleteAddress = async (id: string): Promise<void> => {
  await apiClient.delete(`/addresses/${id}`);
};

export const setDefaultAddress = async (id: string): Promise<Address> => {
  const res = await apiClient.patch(`/addresses/${id}/set-default`);
  return normalizeAddress(res.data.address ?? res.data);
};
