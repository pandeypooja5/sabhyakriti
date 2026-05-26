import apiClient from './apiClient';
import type { Order, Address, PaginatedResponse } from '@/types';

export const createOrder = async (data: {
  addressId: string;
  paymentMethod: string;
  couponCode?: string;
}): Promise<Order> => {
  const res = await apiClient.post('/orders', data);
  return res.data.order ?? res.data;
};

export const listOrders = async (page = 1, pageSize = 10): Promise<PaginatedResponse<Order>> => {
  const res = await apiClient.get('/orders', { params: { page, pageSize } });
  return res.data;
};

export const getOrderDetail = async (orderId: string): Promise<Order> => {
  const res = await apiClient.get(`/orders/${orderId}`);
  return res.data.order ?? res.data;
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
  return res.data.addresses ?? res.data;
};

export const addAddress = async (data: Omit<Address, 'id' | 'userId'>): Promise<Address> => {
  const res = await apiClient.post('/addresses', data);
  return res.data.address ?? res.data;
};

export const updateAddress = async (id: string, data: Partial<Address>): Promise<Address> => {
  const res = await apiClient.patch(`/addresses/${id}`, data);
  return res.data.address ?? res.data;
};

export const deleteAddress = async (id: string): Promise<void> => {
  await apiClient.delete(`/addresses/${id}`);
};

export const setDefaultAddress = async (id: string): Promise<Address> => {
  const res = await apiClient.patch(`/addresses/${id}/default`);
  return res.data.address ?? res.data;
};
