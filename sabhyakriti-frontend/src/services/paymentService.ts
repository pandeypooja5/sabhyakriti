import apiClient from './apiClient';
import type { RazorpayOrderResponse, PaymentVerificationPayload } from '@/types';

export const createRazorpayOrder = async (orderId: string, amount: number): Promise<RazorpayOrderResponse> => {
  const res = await apiClient.post('/payments/create-order', {
    order_id: orderId,
    amount,
    currency: 'INR',
  });
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const d = res.data as any;
  return {
    razorpayOrderId: d.razorpay_order_id ?? d.razorpayOrderId ?? '',
    amount: Number(d.amount ?? 0),
    currency: d.currency ?? 'INR',
    keyId: d.razorpay_key_id ?? d.keyId ?? import.meta.env.VITE_RAZORPAY_KEY_ID ?? '',
  };
};

export const verifyPayment = async (payload: PaymentVerificationPayload): Promise<{ success: boolean; orderId: string }> => {
  const res = await apiClient.post('/payments/verify', {
    order_id: payload.orderId,
    razorpay_order_id: payload.razorpayOrderId,
    razorpay_payment_id: payload.razorpayPaymentId,
    razorpay_signature: payload.razorpaySignature,
  });
  return { success: true, orderId: payload.orderId, ...res.data };
};

export const getPaymentReceipt = async (paymentId: string): Promise<Blob> => {
  const res = await apiClient.get(`/payments/${paymentId}/receipt`, { responseType: 'blob' });
  return res.data;
};
