import apiClient from './apiClient';
import type { Cart, Product } from '@/types';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function normalizeCartResponse(raw: any): Cart {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const items = (raw?.items ?? []) as any[];
  const totals = raw?.totals ?? {};
  return {
    id: String(raw?.cart_id ?? raw?.id ?? ''),
    items: items.map((item) => ({
      id: String(item.cart_item_id ?? item.id ?? ''),
      productId: String(item.product_id ?? ''),
      product: {
        id: String(item.product_id ?? ''),
        name: String(item.product_name ?? ''),
        slug: '',
        sku: '',
        description: '',
        price: Number(item.discounted_price ?? 0),
        mrp: Number(item.discounted_price ?? 0),
        discountPercent: 0,
        stockStatus: item.stock_status ?? 'OUT_OF_STOCK',
        stockQuantity: 0,
        images: item.primary_image_url
          ? [{ url: item.primary_image_url, isPrimary: true, altText: '', id: '', sortOrder: 0 }]
          : [],
        fabric: '',
        blouseIncluded: false,
        careInstructions: '',
        fabricCategories: [],
        occasionCategories: [],
        regionCategories: [],
        avgRating: 0,
        reviewCount: 0,
        isActive: item.is_available ?? false,
        isFeatured: false,
        createdAt: '',
        updatedAt: '',
      } as Product,
      quantity: Number(item.quantity ?? 0),
      unitPrice: Number(item.discounted_price ?? 0),
      subtotal: Number(item.item_total ?? 0),
    })),
    totals: {
      subtotal: Number(totals.subtotal ?? 0),
      discountAmount: Number(totals.discount_amount ?? 0),
      couponDiscount: 0,
      gstAmount: Number(totals.gst_amount ?? 0),
      shippingAmount: Number(totals.shipping_charge ?? 0),
      total: Number(totals.total ?? 0),
      itemCount: items.length,
    },
    couponCode: raw?.coupon_code ?? undefined,
  };
}

export const getCart = async (): Promise<Cart> => {
  const res = await apiClient.get('/cart');
  return normalizeCartResponse(res.data.cart ?? res.data);
};

export const addToCart = async (productId: string, quantity: number): Promise<Cart> => {
  const res = await apiClient.post('/cart/items', { product_id: productId, quantity });
  return normalizeCartResponse(res.data.cart ?? res.data);
};

export const updateQuantity = async (itemId: string, quantity: number): Promise<Cart> => {
  const res = await apiClient.patch(`/cart/items/${itemId}`, { quantity });
  return normalizeCartResponse(res.data.cart ?? res.data);
};

export const removeFromCart = async (itemId: string): Promise<void> => {
  await apiClient.delete(`/cart/items/${itemId}`);
};

export const clearCart = async (): Promise<void> => {
  const cart = await getCart();
  await Promise.all(cart.items.map((item) => apiClient.delete(`/cart/items/${item.id}`)));
};

export const applyCoupon = async (code: string): Promise<Cart> => {
  const res = await apiClient.post('/cart/coupon', { code });
  return normalizeCartResponse(res.data.cart ?? res.data);
};

export const removeCoupon = async (): Promise<Cart> => {
  const res = await apiClient.delete('/cart/coupon');
  return normalizeCartResponse(res.data.cart ?? res.data);
};
