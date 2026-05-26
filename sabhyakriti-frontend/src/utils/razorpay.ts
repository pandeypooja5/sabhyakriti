import type { RazorpayOrderResponse } from '@/types';

declare global {
  interface Window {
    Razorpay: new (options: RazorpayOptions) => RazorpayInstance;
  }
}

interface RazorpayOptions {
  key: string;
  amount: number;
  currency: string;
  name: string;
  description?: string;
  image?: string;
  order_id: string;
  handler: (response: RazorpayPaymentResponse) => void;
  prefill?: {
    name?: string;
    email?: string;
    contact?: string;
  };
  theme?: {
    color?: string;
  };
  modal?: {
    ondismiss?: () => void;
  };
}

interface RazorpayPaymentResponse {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}

interface RazorpayInstance {
  open: () => void;
  on: (event: string, handler: () => void) => void;
}

export interface RazorpayResult {
  success: boolean;
  razorpayOrderId?: string;
  razorpayPaymentId?: string;
  razorpaySignature?: string;
  cancelled?: boolean;
}

/**
 * Load Razorpay SDK script dynamically if not already loaded.
 */
const loadRazorpayScript = (): Promise<boolean> => {
  if (window.Razorpay) return Promise.resolve(true);

  return new Promise((resolve) => {
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
};

/**
 * Open Razorpay checkout widget and return payment result.
 */
export const loadRazorpay = async (
  rzpOrder: RazorpayOrderResponse,
  prefill?: { name?: string; email?: string; contact?: string }
): Promise<RazorpayResult> => {
  const loaded = await loadRazorpayScript();
  if (!loaded) {
    throw new Error('Failed to load Razorpay SDK. Please check your internet connection.');
  }

  return new Promise((resolve) => {
    const options: RazorpayOptions = {
      key: rzpOrder.keyId || import.meta.env.VITE_RAZORPAY_KEY_ID || '',
      amount: rzpOrder.amount,
      currency: rzpOrder.currency || 'INR',
      name: 'Sabhyakriti',
      description: 'Saree Purchase',
      image: '/logo.png',
      order_id: rzpOrder.razorpayOrderId,
      handler: (response) => {
        resolve({
          success: true,
          razorpayOrderId: response.razorpay_order_id,
          razorpayPaymentId: response.razorpay_payment_id,
          razorpaySignature: response.razorpay_signature,
        });
      },
      prefill,
      theme: {
        color: '#FF6B2B',
      },
      modal: {
        ondismiss: () => {
          resolve({ success: false, cancelled: true });
        },
      },
    };

    const rzp = new window.Razorpay(options);
    rzp.on('payment.failed', () => {
      resolve({ success: false });
    });
    rzp.open();
  });
};
