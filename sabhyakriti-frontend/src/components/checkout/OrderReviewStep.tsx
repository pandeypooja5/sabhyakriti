import { useState } from 'react';
import type { Address, PaymentMethod } from '@/types';
import { useCart } from '@/hooks/useCart';
import { formatINR } from '@/utils/currency';
import { CreditCard, MapPin, ShoppingBag } from 'lucide-react';

interface OrderReviewStepProps {
  address: Address;
  paymentMethod: PaymentMethod;
  onBack: () => void;
  onPlaceOrder: () => Promise<void>;
}

const paymentMethodLabels: Record<PaymentMethod, string> = {
  RAZORPAY: 'Card / Net Banking / UPI via Razorpay',
  UPI: 'UPI Direct',
  COD: 'Cash on Delivery',
};

const OrderReviewStep: React.FC<OrderReviewStepProps> = ({
  address, paymentMethod, onBack, onPlaceOrder,
}) => {
  const { items, totals } = useCart();
  const [placing, setPlacing] = useState(false);

  const handlePlace = async () => {
    setPlacing(true);
    try {
      await onPlaceOrder();
    } finally {
      setPlacing(false);
    }
  };

  return (
    <div data-testid="order-review-step">
      <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
        <ShoppingBag className="h-5 w-5 text-saffron-500" /> Review Your Order
      </h2>

      {/* Items */}
      <div className="bg-gray-50 rounded-xl p-4 mb-4 space-y-3">
        {items.map((item) => {
          const img = item.product.images.find((i) => i.isPrimary) ?? item.product.images[0];
          return (
            <div key={item.id} className="flex gap-3" data-testid="review-order-item">
              <img src={img?.url} alt={item.product.name} className="h-14 w-12 object-cover rounded" />
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900 line-clamp-1">{item.product.name}</p>
                <p className="text-xs text-gray-500">Qty: {item.quantity}</p>
              </div>
              <span className="text-sm font-semibold text-gray-900">{formatINR(item.subtotal)}</span>
            </div>
          );
        })}
      </div>

      {/* Address */}
      <div className="bg-gray-50 rounded-xl p-4 mb-4">
        <h3 className="text-sm font-semibold text-gray-800 mb-2 flex items-center gap-1">
          <MapPin className="h-4 w-4 text-saffron-500" /> Delivery Address
        </h3>
        <p className="text-sm text-gray-700">{address.name}</p>
        <p className="text-sm text-gray-600">{address.line1}{address.line2 ? `, ${address.line2}` : ''}</p>
        <p className="text-sm text-gray-600">{address.city}, {address.state} — {address.pincode}</p>
        <p className="text-sm text-gray-500">{address.phone}</p>
      </div>

      {/* Payment */}
      <div className="bg-gray-50 rounded-xl p-4 mb-4">
        <h3 className="text-sm font-semibold text-gray-800 mb-1 flex items-center gap-1">
          <CreditCard className="h-4 w-4 text-saffron-500" /> Payment
        </h3>
        <p className="text-sm text-gray-700">{paymentMethodLabels[paymentMethod]}</p>
      </div>

      {/* Totals */}
      {totals && (
        <div className="space-y-1.5 text-sm mb-6">
          <div className="flex justify-between text-gray-600">
            <span>Subtotal</span><span>{formatINR(totals.subtotal)}</span>
          </div>
          {totals.couponDiscount > 0 && (
            <div className="flex justify-between text-green-600">
              <span>Coupon Discount</span><span>-{formatINR(totals.couponDiscount)}</span>
            </div>
          )}
          <div className="flex justify-between text-gray-600">
            <span>GST</span><span>{formatINR(totals.gstAmount)}</span>
          </div>
          <div className="flex justify-between text-gray-600">
            <span>Shipping</span><span className={totals.shippingAmount === 0 ? 'text-green-600' : ''}>{totals.shippingAmount === 0 ? 'FREE' : formatINR(totals.shippingAmount)}</span>
          </div>
          <div className="flex justify-between font-bold text-gray-900 text-base border-t border-gray-200 pt-2">
            <span>Total</span><span>{formatINR(totals.total)}</span>
          </div>
        </div>
      )}

      <div className="flex gap-3">
        <button
          onClick={onBack}
          data-testid="review-back-btn"
          className="flex-1 py-3 border border-gray-300 text-gray-700 font-medium rounded-xl hover:bg-gray-50"
        >
          Back
        </button>
        <button
          onClick={handlePlace}
          disabled={placing}
          data-testid="place-order-btn"
          className="flex-1 py-3 bg-saffron-500 hover:bg-saffron-600 text-white font-semibold rounded-xl disabled:opacity-60 transition-colors shadow-md"
        >
          {placing ? 'Placing Order...' : 'Place Order'}
        </button>
      </div>
    </div>
  );
};

export default OrderReviewStep;
