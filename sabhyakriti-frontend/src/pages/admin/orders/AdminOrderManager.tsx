import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search } from 'lucide-react';
import type { Order, OrderStatus } from '@/types';
import { listAllOrders } from '@/services/adminService';
import { formatDate } from '@/utils/date';
import { formatINR } from '@/utils/currency';
import LoadingSpinner from '@/components/shared/LoadingSpinner';
import { cn } from '@/lib/utils';

const statusFilters: (OrderStatus | '')[] = ['', 'PENDING', 'CONFIRMED', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'RETURN_REQUESTED'];

const statusColors: Record<string, string> = {
  PENDING: 'bg-amber-100 text-amber-700', CONFIRMED: 'bg-blue-100 text-blue-700',
  PROCESSING: 'bg-blue-100 text-blue-700', SHIPPED: 'bg-purple-100 text-purple-700',
  DELIVERED: 'bg-green-100 text-green-700', CANCELLED: 'bg-red-100 text-red-700',
  RETURN_REQUESTED: 'bg-orange-100 text-orange-700',
};

const AdminOrderManager: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<OrderStatus | ''>('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    setLoading(true);
    listAllOrders(page, statusFilter || undefined, search || undefined)
      .then((res) => { setOrders(res.data); setTotal(res.total); })
      .catch(() => null)
      .finally(() => setLoading(false));
  }, [page, statusFilter, search]);

  return (
    <div data-testid="admin-order-manager">
      <h1 className="text-xl font-bold text-gray-900 mb-6">Orders ({total})</h1>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <div className="relative max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} placeholder="Search by order #..." data-testid="order-search" className="input-field pl-9" />
        </div>
        <div className="flex gap-1 overflow-x-auto">
          {statusFilters.map((s) => (
            <button
              key={s}
              onClick={() => { setStatusFilter(s); setPage(1); }}
              data-testid={`filter-${s || 'all'}`}
              className={cn('px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors', statusFilter === s ? 'bg-teal-700 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200')}
            >
              {s || 'All'}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-16"><LoadingSpinner /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  {['Order #', 'Customer', 'Date', 'Status', 'Items', 'Total', 'Action'].map((h) => (
                    <th key={h} className="text-left px-4 py-3 font-semibold text-gray-600 whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {orders.map((order) => (
                  <tr key={order.id} className="hover:bg-gray-50" data-testid="admin-order-row">
                    <td className="px-4 py-3 font-mono text-sm">#{order.orderNumber}</td>
                    <td className="px-4 py-3">{order.shippingAddress.name}</td>
                    <td className="px-4 py-3 text-gray-500">{formatDate(order.createdAt)}</td>
                    <td className="px-4 py-3">
                      <span className={cn('px-2.5 py-0.5 rounded-full text-xs font-medium', statusColors[order.status] ?? 'bg-gray-100 text-gray-700')}>
                        {order.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600">{order.items.length}</td>
                    <td className="px-4 py-3 font-semibold">{formatINR(order.total)}</td>
                    <td className="px-4 py-3">
                      <Link to={`/admin/orders/${order.id}`} data-testid={`admin-view-order-${order.id}`} className="text-xs font-medium text-teal-700 hover:text-teal-900">
                        View →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {total > 20 && (
        <div className="flex justify-center gap-2 mt-4">
          <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)} className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-40">Prev</button>
          <span className="px-3 py-1.5 text-sm text-gray-500">Page {page}</span>
          <button onClick={() => setPage((p) => p + 1)} className="px-3 py-1.5 text-sm border rounded-lg">Next</button>
        </div>
      )}
    </div>
  );
};

export default AdminOrderManager;
