import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import type { Order, OrderStatus } from '@/types';
import { getOrderDetail } from '@/services/orderService';
import { updateOrderStatus } from '@/services/adminService';
import { formatDate } from '@/utils/date';
import { formatINR } from '@/utils/currency';
import OrderStatusTimeline from '@/components/order/OrderStatusTimeline';
import LoadingSpinner from '@/components/shared/LoadingSpinner';
import toast from 'react-hot-toast';

const nextStatuses: Record<string, OrderStatus[]> = {
  PENDING: ['CONFIRMED', 'CANCELLED'],
  CONFIRMED: ['PROCESSING', 'CANCELLED'],
  PROCESSING: ['SHIPPED'],
  SHIPPED: ['OUT_FOR_DELIVERY'],
  OUT_FOR_DELIVERY: ['DELIVERED'],
};

const AdminOrderDetail: React.FC = () => {
  const { orderId } = useParams<{ orderId: string }>();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [newStatus, setNewStatus] = useState<OrderStatus | ''>('');
  const [trackingNumber, setTrackingNumber] = useState('');
  const [courierName, setCourierName] = useState('');
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    if (!orderId) return;
    getOrderDetail(orderId)
      .then(setOrder)
      .finally(() => setLoading(false));
  }, [orderId]);

  const handleUpdate = async () => {
    if (!order || !newStatus) return;
    setUpdating(true);
    try {
      const updated = await updateOrderStatus(order.id, newStatus, trackingNumber || undefined, courierName || undefined);
      setOrder(updated);
      toast.success(`Order status updated to ${newStatus}`);
      setNewStatus('');
    } catch {
      toast.error('Failed to update status');
    } finally {
      setUpdating(false);
    }
  };

  if (loading) return <div className="flex justify-center py-20"><LoadingSpinner size="lg" /></div>;
  if (!order) return <div className="text-center py-20 text-gray-500">Order not found</div>;

  const allowedNext = nextStatuses[order.status] ?? [];

  return (
    <div data-testid="admin-order-detail" className="max-w-4xl">
      <Link to="/admin/orders" className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-4">
        <ArrowLeft className="h-4 w-4" /> All Orders
      </Link>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Order #{order.orderNumber}</h1>
          <p className="text-sm text-gray-500">Placed {formatDate(order.createdAt)}</p>
        </div>
        <span className="px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-700">{order.status}</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Timeline */}
        <div className="bg-white rounded-2xl border border-gray-100 p-5">
          <h2 className="font-bold text-gray-800 mb-2">Status Timeline</h2>
          <OrderStatusTimeline currentStatus={order.status} history={order.statusHistory} />

          {/* Update Status Form */}
          {allowedNext.length > 0 && (
            <div className="mt-4 border-t pt-4 space-y-3" data-testid="update-status-form">
              <h3 className="text-sm font-semibold text-gray-700">Update Status</h3>
              <select
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value as OrderStatus)}
                className="input-field text-sm"
                data-testid="status-select"
              >
                <option value="">Select status...</option>
                {allowedNext.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
              {(newStatus === 'SHIPPED' || newStatus === 'OUT_FOR_DELIVERY') && (
                <>
                  <input value={trackingNumber} onChange={(e) => setTrackingNumber(e.target.value)} placeholder="Tracking Number" className="input-field text-sm" data-testid="tracking-input" />
                  <input value={courierName} onChange={(e) => setCourierName(e.target.value)} placeholder="Courier Name" className="input-field text-sm" data-testid="courier-input" />
                </>
              )}
              <button
                onClick={handleUpdate}
                disabled={!newStatus || updating}
                data-testid="update-status-btn"
                className="w-full py-2 bg-teal-700 text-white text-sm font-medium rounded-xl hover:bg-teal-800 disabled:opacity-50"
              >
                {updating ? 'Updating...' : 'Update Status'}
              </button>
            </div>
          )}
        </div>

        <div className="lg:col-span-2 space-y-4">
          {/* Items */}
          <div className="bg-white rounded-2xl border border-gray-100 p-5">
            <h2 className="font-bold text-gray-800 mb-3">Items</h2>
            {order.items.map((item) => (
              <div key={item.id} className="flex gap-3 py-2 border-b last:border-0">
                <img src={item.product.images[0]?.url} alt={item.product.name} className="h-12 w-10 object-cover rounded" />
                <div className="flex-1">
                  <p className="text-sm font-medium">{item.product.name}</p>
                  <p className="text-xs text-gray-500">Qty: {item.quantity}</p>
                </div>
                <span className="text-sm font-semibold">{formatINR(item.subtotal)}</span>
              </div>
            ))}
          </div>

          {/* Customer */}
          <div className="bg-white rounded-2xl border border-gray-100 p-5">
            <h2 className="font-bold text-gray-800 mb-2">Shipping Address</h2>
            <p className="text-sm text-gray-700">{order.shippingAddress.name} · {order.shippingAddress.phone}</p>
            <p className="text-sm text-gray-600">{order.shippingAddress.line1}, {order.shippingAddress.city}, {order.shippingAddress.state} — {order.shippingAddress.pincode}</p>
          </div>

          {/* Totals */}
          <div className="bg-white rounded-2xl border border-gray-100 p-5 space-y-1 text-sm">
            <div className="flex justify-between"><span className="text-gray-500">Subtotal</span><span>{formatINR(order.subtotal)}</span></div>
            <div className="flex justify-between"><span className="text-gray-500">GST</span><span>{formatINR(order.gstAmount)}</span></div>
            <div className="flex justify-between"><span className="text-gray-500">Shipping</span><span>{order.shippingAmount === 0 ? 'FREE' : formatINR(order.shippingAmount)}</span></div>
            <div className="flex justify-between font-bold text-gray-900 border-t pt-1"><span>Total</span><span>{formatINR(order.total)}</span></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminOrderDetail;
