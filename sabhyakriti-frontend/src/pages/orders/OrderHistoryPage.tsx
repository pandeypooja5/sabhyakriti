import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Package } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '@/store/store';
import { fetchOrders } from '@/store/slices/orderSlice';
import { formatDate } from '@/utils/date';
import { formatINR } from '@/utils/currency';
import EmptyState from '@/components/shared/EmptyState';
import LoadingSpinner from '@/components/shared/LoadingSpinner';
import Breadcrumb from '@/components/shared/Breadcrumb';
import { cn } from '@/lib/utils';

const statusColors: Record<string, string> = {
  PENDING: 'bg-amber-100 text-amber-700',
  CONFIRMED: 'bg-blue-100 text-blue-700',
  PROCESSING: 'bg-blue-100 text-blue-700',
  SHIPPED: 'bg-purple-100 text-purple-700',
  OUT_FOR_DELIVERY: 'bg-orange-100 text-orange-700',
  DELIVERED: 'bg-green-100 text-green-700',
  CANCELLED: 'bg-red-100 text-red-700',
  RETURN_REQUESTED: 'bg-orange-100 text-orange-700',
  RETURNED: 'bg-gray-100 text-gray-700',
  REFUNDED: 'bg-teal-100 text-teal-700',
};

const OrderHistoryPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { orders, loading, total, page } = useAppSelector((s) => s.orders);

  useEffect(() => {
    dispatch(fetchOrders({ page: 1, pageSize: 10 }));
  }, [dispatch]);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6" data-testid="order-history-page">
      <Breadcrumb items={[{ label: 'My Orders' }]} />
      <h1 className="text-2xl font-bold text-gray-900 mt-4 mb-6 flex items-center gap-2">
        <Package className="h-6 w-6" /> My Orders
        {total > 0 && <span className="text-base font-normal text-gray-500">({total} orders)</span>}
      </h1>

      {loading ? (
        <div className="flex justify-center py-20"><LoadingSpinner size="lg" /></div>
      ) : orders.length === 0 ? (
        <EmptyState
          icon={<Package className="h-16 w-16" />}
          title="No orders yet"
          message="Your orders will appear here after you make a purchase."
          ctaLabel="Start Shopping"
          ctaHref="/sarees"
        />
      ) : (
        <div className="space-y-4">
          {orders.map((order) => (
            <div
              key={order.id}
              className="bg-white rounded-2xl border border-gray-100 p-4 hover:shadow-sm transition-shadow"
              data-testid="order-summary-card"
            >
              <div className="flex items-start justify-between gap-4 mb-3">
                <div>
                  <p className="text-sm font-bold text-gray-900">#{order.orderNumber}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{formatDate(order.createdAt)}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={cn('text-xs font-medium px-2.5 py-1 rounded-full', statusColors[order.status] ?? 'bg-gray-100 text-gray-700')}>
                    {order.status.replace('_', ' ')}
                  </span>
                  <span className="font-bold text-gray-900">{formatINR(order.total)}</span>
                </div>
              </div>

              {/* Items preview */}
              <div className="flex gap-2 mb-3">
                {order.items.slice(0, 3).map((item) => (
                  <img
                    key={item.id}
                    src={item.product.images[0]?.url ?? '/placeholder.jpg'}
                    alt={item.product.name}
                    className="h-14 w-12 object-cover rounded-lg"
                  />
                ))}
                {order.items.length > 3 && (
                  <div className="h-14 w-12 rounded-lg bg-gray-100 flex items-center justify-center text-xs text-gray-500">
                    +{order.items.length - 3}
                  </div>
                )}
              </div>

              <Link
                to={`/orders/${order.id}`}
                data-testid="view-order-btn"
                className="text-sm font-medium text-saffron-500 hover:text-saffron-600"
              >
                View Details →
              </Link>
            </div>
          ))}

          {/* Simple pagination */}
          {total > 10 && (
            <div className="flex justify-center gap-2 pt-2">
              <button
                disabled={page <= 1}
                onClick={() => dispatch(fetchOrders({ page: page - 1 }))}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-40"
              >
                Prev
              </button>
              <button
                onClick={() => dispatch(fetchOrders({ page: page + 1 }))}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg"
              >
                Next
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default OrderHistoryPage;
