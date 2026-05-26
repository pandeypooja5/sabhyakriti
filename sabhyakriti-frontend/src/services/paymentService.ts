import apiClient from './apiClient';
import type { RazorpayOrderResponse, PaymentVerificationPayload } from '@/types';

export const createRazorpayOrder = async (orderId: string): Promise<RazorpayOrderResponse> => {
  const res = await apiClient.post('/payments/razorpay/create', { orderId });
  return res.data;
};

export const verifyPayment = async (payload: PaymentVerificationPayload): Promise<{ success: boolean; orderId: string }> => {
  const res = await apiClient.post('/payments/razorpay/verify', payload);
  return res.data;
};

export const getPaymentReceipt = async (paymentId: string): Promise<Blob> => {
  const res = await apiClient.get(`/payments/${paymentId}/receipt`, { responseType: 'blob' });
  return res.data;
};
