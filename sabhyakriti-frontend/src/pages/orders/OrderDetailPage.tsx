import { useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/store/store';
import { fetchOrderDetail } from '@/store/slices/orderSlice';
import { openCancelOrderModal, openReturnModal } from '@/store/slices/uiSlice';
import { formatDate } from '@/utils/date';
import { formatINR } from '@/utils/currency';
import OrderStatusTimeline from '@/components/order/OrderStatusTimeline';
import CancelOrderModal from '@/components/order/CancelOrderModal';
import ReturnRequestModal from '@/components/order/ReturnRequestModal';
import InvoiceDownloadButton from '@/components/order/InvoiceDownloadButton';
import Breadcrumb from '@/components/shared/Breadcrumb';
import LoadingSpinner from '@/components/shared/LoadingSpinner';
import { useOrderPolling } from '@/hooks/useOrderPolling';

const OrderDetailPage: React.FC = () => {
  const { orderId } = useParams<{ orderId: string }>();
  const dispatch = useAppDispatch();
  const { currentOrder, loading } = useAppSelector((s) => s.orders);

  useEffect(() => {
    if (orderId) dispatch(fetchOrderDetail(orderId));
  }, [dispatch, orderId]);

  useOrderPolling(orderId ?? null, currentOrder?.status);

  if (loading) return <div className="flex justify-center py-20"><LoadingSpinner size="lg" /></div>;
  if (!currentOrder) return <div className="text-center py-20 text-gray-500">Order not found</div>;

  const canCancel = ['PENDING', 'CONFIRMED'].includes(currentOrder.status);
  const canReturn = currentOrder.status === 'DELIVERED';

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6" data-testid="order-detail-page">
      <Breadcrumb items={[{ label: 'Orders', href: '/orders' }, { label: `#${currentOrder.orderNumber}` }]} />

      <div className="flex items-center justify-between mt-4 mb-6 flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Order #{currentOrder.orderNumber}</h1>
          <p className="text-sm text-gray-500 mt-0.5">Placed on {formatDate(currentOrder.createdAt)}</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <InvoiceDownloadButton orderId={currentOrder.id} orderNumber={currentOrder.orderNumber} />
          {canCancel && (
            <button
              onClick={() => dispatch(openCancelOrderModal(currentOrder.id))}
              data-testid="cancel-order-btn"
              className="px-4 py-2 border border-red-300 text-red-600 text-sm font-medium rounded-xl hover:bg-red-50 transition-colors"
            >
              Cancel Order
            </button>
          )}
          {canReturn && (
            <button
              onClick={() => dispatch(openReturnModal(currentOrder.id))}
              data-testid="return-order-btn"
              className="px-4 py-2 border border-saffron-300 text-saffron-600 text-sm font-medium rounded-xl hover:bg-saffron-50 transition-colors"
            >
              Return Items
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Timeline */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-2xl border border-gray-100 p-5">
            <h2 className="font-bold text-gray-800 mb-2">Order Status</h2>
            <OrderStatusTimeline
              currentStatus={currentOrder.status}
              history={currentOrder.statusHistory}
            />
            {currentOrder.trackingNumber && (
              <div className="mt-3 p-3 bg-blue-50 rounded-xl">
                <p className="text-xs text-blue-700 font-medium">Tracking</p>
                <p className="text-sm font-semibold text-blue-900">{currentOrder.trackingNumber}</p>
                {currentOrder.courierName && (
                  <p className="text-xs text-blue-600">{currentOrder.courierName}</p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right column */}
        <div className="lg:col-span-2 space-y-4">
          {/* Items */}
          <div className="bg-white rounded-2xl border border-gray-100 p-5">
            <h2 className="font-bold text-gray-800 mb-3">Items ({currentOrder.items.length})</h2>
            {currentOrder.items.map((item) => (
              <div key={item.id} className="flex gap-3 py-3 border-b last:border-0" data-testid="order-item">
                <img
                  src={item.product.images[0]?.url ?? '/placeholder.jpg'}
                  alt={item.product.name}
                  className="h-16 w-14 object-cover rounded-lg"
                />
                <div className="flex-1">
                  <Link
                    to={`/sarees/${item.product.slug}`}
                    className="text-sm font-medium text-gray-900 hover:text-saffron-500"
                  >
                    {item.product.name}
                  </Link>
                  <p className="text-xs text-gray-500">Qty: {item.quantity}</p>
                </div>
                <span className="text-sm font-bold text-gray-900">{formatINR(item.subtotal)}</span>
              </div>
            ))}
          </div>

          {/* Shipping address */}
          <div className="bg-white rounded-2xl border border-gray-100 p-5">
            <h2 className="font-bold text-gray-800 mb-2">Delivery Address</h2>
            <p className="text-sm text-gray-700">{currentOrder.shippingAddress.name}</p>
            <p className="text-sm text-gray-600">{currentOrder.shippingAddress.line1}</p>
            <p className="text-sm text-gray-600">
              {currentOrder.shippingAddress.city}, {currentOrder.shippingAddress.state} — {currentOrder.shippingAddress.pincode}
            </p>
            <p className="text-sm text-gray-500">{currentOrder.shippingAddress.phone}</p>
          </div>

          {/* Totals */}
          <div className="bg-white rounded-2xl border border-gray-100 p-5 space-y-1.5 text-sm">
            <div className="flex justify-between text-gray-600"><span>Subtotal</span><span>{formatINR(currentOrder.subtotal)}</span></div>
            {currentOrder.discountAmount > 0 && (
              <div className="flex justify-between text-green-600"><span>Discount</span><span>-{formatINR(currentOrder.discountAmount)}</span></div>
            )}
            {currentOrder.couponDiscount > 0 && (
              <div className="flex justify-between text-green-600">
                <span>Coupon ({currentOrder.couponCode})</span>
                <span>-{formatINR(currentOrder.couponDiscount)}</span>
              </div>
            )}
            <div className="flex justify-between text-gray-600"><span>GST</span><span>{formatINR(currentOrder.gstAmount)}</span></div>
            <div className="flex justify-between text-gray-600"><span>Shipping</span><span>{currentOrder.shippingAmount === 0 ? 'FREE' : formatINR(currentOrder.shippingAmount)}</span></div>
            <div className="flex justify-between font-bold text-gray-900 text-base border-t pt-2">
              <span>Total</span><span>{formatINR(currentOrder.total)}</span>
            </div>
          </div>
        </div>
      </div>

      <CancelOrderModal />
      <ReturnRequestModal />
    </div>
  );
};

export default OrderDetailPage;
