import { Link } from 'react-router-dom';
import { ShieldCheck, Truck } from 'lucide-react';
import { useCart } from '@/hooks/useCart';
import { formatINR } from '@/utils/currency';
import CouponInput from './CouponInput';

interface CartSummaryProps {
  showCheckoutBtn?: boolean;
}

const CartSummary: React.FC<CartSummaryProps> = ({ showCheckoutBtn = true }) => {
  const { totals, couponCode } = useCart();

  if (!totals) return null;

  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5 space-y-4" data-testid="cart-summary">
      <h2 className="font-bold text-gray-900 text-base">Order Summary</h2>

      {/* Coupon */}
      <CouponInput />

      {/* Price breakdown */}
      <div className="space-y-2 text-sm">
        <div className="flex justify-between text-gray-600">
          <span>Subtotal ({totals.itemCount} items)</span>
          <span data-testid="summary-subtotal">{formatINR(totals.subtotal)}</span>
        </div>

        {totals.discountAmount > 0 && (
          <div className="flex justify-between text-green-600">
            <span>Product Discount</span>
            <span data-testid="summary-discount">-{formatINR(totals.discountAmount)}</span>
          </div>
        )}

        {couponCode && totals.couponDiscount > 0 && (
          <div className="flex justify-between text-green-600">
            <span>Coupon ({couponCode})</span>
            <span data-testid="summary-coupon">-{formatINR(totals.couponDiscount)}</span>
          </div>
        )}

        <div className="flex justify-between text-gray-600">
          <span>GST (5%)</span>
          <span data-testid="summary-gst">{formatINR(totals.gstAmount)}</span>
        </div>

        <div className="flex justify-between text-gray-600">
          <span>Shipping</span>
          <span data-testid="summary-shipping" className={totals.shippingAmount === 0 ? 'text-green-600 font-medium' : ''}>
            {totals.shippingAmount === 0 ? 'FREE' : formatINR(totals.shippingAmount)}
          </span>
        </div>

        <div className="border-t border-gray-100 pt-2 mt-2 flex justify-between font-bold text-gray-900 text-base">
          <span>Total</span>
          <span data-testid="summary-total">{formatINR(totals.total)}</span>
        </div>
      </div>

      {/* Trust badges */}
      <div className="space-y-2 pt-1">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <Truck className="h-3.5 w-3.5 text-green-500 flex-shrink-0" />
          <span>Free shipping on orders above ₹999</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <ShieldCheck className="h-3.5 w-3.5 text-blue-500 flex-shrink-0" />
          <span>Secure payment · Easy 30-day returns</span>
        </div>
      </div>

      {showCheckoutBtn && (
        <Link
          to="/checkout"
          data-testid="checkout-btn"
          className="block w-full text-center py-3 bg-saffron-500 hover:bg-saffron-600 text-white font-semibold rounded-xl transition-colors shadow-md"
        >
          Proceed to Checkout
        </Link>
      )}
    </div>
  );
};

export default CartSummary;
