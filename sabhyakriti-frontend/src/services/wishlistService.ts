import apiClient from './apiClient';
import type { WishlistItem } from '@/types';

export const getWishlist = async (): Promise<WishlistItem[]> => {
  const res = await apiClient.get('/wishlist');
  return res.data.items ?? res.data;
};

export const addToWishlist = async (productId: string): Promise<WishlistItem> => {
  const res = await apiClient.post('/wishlist', { productId });
  return res.data.item ?? res.data;
};

export const removeFromWishlist = async (productId: string): Promise<void> => {
  await apiClient.delete(`/wishlist/${productId}`);
};
