import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { CheckCircle, Package, ChevronRight } from 'lucide-react';
import type { Order } from '@/types';
import { getOrderDetail } from '@/services/orderService';
import { formatDate } from '@/utils/date';
import { formatINR } from '@/utils/currency';
import LoadingSpinner from '@/components/shared/LoadingSpinner';

const OrderConfirmationPage: React.FC = () => {
  const { orderId } = useParams<{ orderId: string }>();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!orderId) return;
    getOrderDetail(orderId)
      .then(setOrder)
      .catch(() => null)
      .finally(() => setLoading(false));
  }, [orderId]);

  if (loading) return <div className="flex justify-center py-20"><LoadingSpinner size="lg" /></div>;

  return (
    <div className="max-w-2xl mx-auto px-4 py-12 text-center" data-testid="order-confirmation-page">
      {/* Success animation */}
      <div className="flex justify-center mb-6">
        <div className="h-20 w-20 rounded-full bg-green-100 flex items-center justify-center animate-fade-in">
          <CheckCircle className="h-12 w-12 text-green-500" />
        </div>
      </div>

      <h1 className="text-3xl font-bold text-gray-900 mb-2">Order Placed!</h1>
      <p className="text-gray-500 mb-4">
        Thank you for your order. We'll send you a confirmation email shortly.
      </p>

      {order && (
        <div className="bg-white rounded-2xl border border-gray-100 p-6 text-left mt-6 space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Order Number</span>
            <span className="font-bold text-gray-900" data-testid="order-number">#{order.orderNumber}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Estimated Delivery</span>
            <span className="font-medium text-gray-900">
              {order.estimatedDelivery ? formatDate(order.estimatedDelivery) : '5-7 business days'}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Total Paid</span>
            <span className="font-bold text-saffron-600">{formatINR(order.total)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Payment Method</span>
            <span className="font-medium text-gray-900">{order.paymentMethod}</span>
          </div>
        </div>
      )}

      <div className="flex flex-col sm:flex-row gap-3 mt-8 justify-center">
        <Link
          to={`/orders/${orderId}`}
          data-testid="track-order-btn"
          className="flex items-center justify-center gap-2 px-6 py-3 bg-teal-700 text-white font-semibold rounded-xl hover:bg-teal-800 transition-colors"
        >
          <Package className="h-4 w-4" /> Track Order
        </Link>
        <Link
          to="/sarees"
          data-testid="continue-shopping-btn"
          className="flex items-center justify-center gap-2 px-6 py-3 border-2 border-gray-300 text-gray-700 font-semibold rounded-xl hover:bg-gray-50 transition-colors"
        >
          Continue Shopping <ChevronRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
};

export default OrderConfirmationPage;
