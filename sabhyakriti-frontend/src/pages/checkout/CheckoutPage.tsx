import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Address, PaymentMethod } from '@/types';
import { createOrder } from '@/services/orderService';
import { createRazorpayOrder, verifyPayment } from '@/services/paymentService';
import { listAddresses } from '@/services/orderService';
import { clearCart as clearCartApi } from '@/services/cartService';
import { loadRazorpay } from '@/utils/razorpay';
import { useAuth } from '@/hooks/useAuth';
import { useCart } from '@/hooks/useCart';
import AddressStep from '@/components/checkout/AddressStep';
import PaymentStep from '@/components/checkout/PaymentStep';
import OrderReviewStep from '@/components/checkout/OrderReviewStep';
import Breadcrumb from '@/components/shared/Breadcrumb';
import { cn } from '@/lib/utils';
import toast from 'react-hot-toast';

const steps = ['Address', 'Payment', 'Review'];

const CheckoutPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { couponCode, refetchCart, items, totals } = useCart();

  const [currentStep, setCurrentStep] = useState(0);
  const [selectedAddressId, setSelectedAddressId] = useState<string | null>(null);
  const [selectedAddress, setSelectedAddress] = useState<Address | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('RAZORPAY');

  const handleAddressNext = async (addressId: string) => {
    setSelectedAddressId(addressId);
    // fetch address details for review step
    const addrs = await listAddresses();
    const addr = addrs.find((a) => a.id === addressId);
    if (addr) setSelectedAddress(addr);
    setCurrentStep(1);
  };

  const handlePaymentNext = (method: PaymentMethod) => {
    setPaymentMethod(method);
    setCurrentStep(2);
  };

  const handlePlaceOrder = async () => {
    if (!selectedAddressId) return;

    if (!totals || items.length === 0) {
      toast.error('Your cart is empty');
      return;
    }

    try {
      const order = await createOrder({
        addressId: selectedAddressId,
        paymentMethod,
        couponCode: couponCode ?? undefined,
        cart: { id: '', items, totals, couponCode: couponCode ?? undefined },
      });

      if (paymentMethod === 'COD') {
        await clearCartApi();
        await refetchCart();
        navigate(`/order-confirmation/${order.id}`);
        return;
      }

      // Razorpay / UPI
      const rzpOrder = await createRazorpayOrder(order.id);
      const result = await loadRazorpay(rzpOrder, {
        name: user?.name,
        email: user?.email,
        contact: user?.phone,
      });

      if (result.cancelled) {
        toast.error('Payment cancelled');
        return;
      }

      if (!result.success || !result.razorpayOrderId || !result.razorpayPaymentId || !result.razorpaySignature) {
        toast.error('Payment failed. Please try again.');
        return;
      }

      await verifyPayment({
        razorpayOrderId: result.razorpayOrderId,
        razorpayPaymentId: result.razorpayPaymentId,
        razorpaySignature: result.razorpaySignature,
        orderId: order.id,
      });

      await clearCartApi();
      await refetchCart();
      navigate(`/order-confirmation/${order.id}`);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      toast.error(error.response?.data?.message ?? 'Order placement failed');
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6" data-testid="checkout-page">
      <Breadcrumb items={[{ label: 'Cart', href: '/cart' }, { label: 'Checkout' }]} />

      <h1 className="text-2xl font-bold text-gray-900 mt-4 mb-6">Checkout</h1>

      {/* Stepper */}
      <div className="flex items-center mb-8">
        {steps.map((step, idx) => (
          <div key={step} className="flex items-center flex-1">
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  'h-8 w-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors',
                  idx < currentStep ? 'bg-green-500 text-white' :
                  idx === currentStep ? 'bg-saffron-500 text-white' :
                  'bg-gray-200 text-gray-500'
                )}
                data-testid={`step-indicator-${idx}`}
              >
                {idx < currentStep ? '✓' : idx + 1}
              </div>
              <span className={cn('text-xs mt-1 font-medium', idx === currentStep ? 'text-saffron-600' : 'text-gray-400')}>
                {step}
              </span>
            </div>
            {idx < steps.length - 1 && (
              <div className={cn('flex-1 h-0.5 mx-2 mb-4 transition-colors', idx < currentStep ? 'bg-green-500' : 'bg-gray-200')} />
            )}
          </div>
        ))}
      </div>

      {/* Step content */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6">
        {currentStep === 0 && (
          <AddressStep onNext={handleAddressNext} />
        )}
        {currentStep === 1 && (
          <PaymentStep
            onNext={handlePaymentNext}
            onBack={() => setCurrentStep(0)}
          />
        )}
        {currentStep === 2 && selectedAddress && (
          <OrderReviewStep
            address={selectedAddress}
            paymentMethod={paymentMethod}
            onBack={() => setCurrentStep(1)}
            onPlaceOrder={handlePlaceOrder}
          />
        )}
      </div>
    </div>
  );
};

export default CheckoutPage;
