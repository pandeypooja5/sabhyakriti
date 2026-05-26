import apiClient from './apiClient';
import type { Review, PaginatedResponse } from '@/types';

export const listReviews = async (productId: string, page = 1, pageSize = 10): Promise<PaginatedResponse<Review>> => {
  const res = await apiClient.get(`/products/${productId}/reviews`, { params: { page, pageSize } });
  return res.data;
};

export const submitReview = async (data: {
  productId: string;
  rating: number;
  title: string;
  body: string;
}): Promise<Review> => {
  const res = await apiClient.post(`/products/${data.productId}/reviews`, data);
  return res.data.review ?? res.data;
};

export const deleteReview = async (productId: string, reviewId: string): Promise<void> => {
  await apiClient.delete(`/products/${productId}/reviews/${reviewId}`);
};
