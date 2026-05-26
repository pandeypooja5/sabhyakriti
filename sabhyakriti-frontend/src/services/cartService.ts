import apiClient from './apiClient';
import type { Cart } from '@/types';

export const getCart = async (): Promise<Cart> => {
  const res = await apiClient.get('/cart');
  return res.data.cart ?? res.data;
};

export const addToCart = async (productId: string, quantity: number): Promise<Cart> => {
  const res = await apiClient.post('/cart/items', { productId, quantity });
  return res.data.cart ?? res.data;
};

export const updateQuantity = async (itemId: string, quantity: number): Promise<Cart> => {
  const res = await apiClient.patch(`/cart/items/${itemId}`, { quantity });
  return res.data.cart ?? res.data;
};

export const removeFromCart = async (itemId: string): Promise<void> => {
  await apiClient.delete(`/cart/items/${itemId}`);
};

export const applyCoupon = async (code: string): Promise<Cart> => {
  const res = await apiClient.post('/cart/coupon', { code });
  return res.data.cart ?? res.data;
};

export const removeCoupon = async (): Promise<Cart> => {
  const res = await apiClient.delete('/cart/coupon');
  return res.data.cart ?? res.data;
};
