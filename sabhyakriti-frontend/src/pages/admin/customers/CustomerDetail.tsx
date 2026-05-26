import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import type { User, Order } from '@/types';
import { getCustomerDetail } from '@/services/adminService';
import { formatDate } from '@/utils/date';
import { formatINR } from '@/utils/currency';
import LoadingSpinner from '@/components/shared/LoadingSpinner';

const CustomerDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<{ user: User; orders: Order[] } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    getCustomerDetail(id).then(setData).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="flex justify-center py-20"><LoadingSpinner size="lg" /></div>;
  if (!data) return <div className="text-center py-20 text-gray-500">Customer not found</div>;

  const { user, orders } = data;
  const totalSpent = orders.reduce((sum, o) => sum + o.total, 0);

  return (
    <div data-testid="customer-detail" className="max-w-3xl">
      <Link to="/admin/customers" className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-4">
        <ArrowLeft className="h-4 w-4" /> All Customers
      </Link>

      <div className="bg-white rounded-2xl border border-gray-100 p-6 mb-4">
        <div className="flex items-center gap-4 mb-4">
          <div className="h-14 w-14 rounded-full bg-teal-100 flex items-center justify-center text-teal-700 font-bold text-xl">
            {user.name[0]}
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">{user.name}</h1>
            <p className="text-sm text-gray-500">{user.email}</p>
            {user.phone && <p className="text-sm text-gray-500">{user.phone}</p>}
          </div>
        </div>
        <div className="grid grid-cols-3 gap-4 border-t pt-4">
          <div className="text-center">
            <p className="text-xl font-bold text-gray-900">{orders.length}</p>
            <p className="text-xs text-gray-500">Orders</p>
          </div>
          <div className="text-center">
            <p className="text-xl font-bold text-saffron-500">{formatINR(totalSpent)}</p>
            <p className="text-xs text-gray-500">Total Spent</p>
          </div>
          <div className="text-center">
            <p className="text-xl font-bold text-gray-900">{formatDate(user.createdAt)}</p>
            <p className="text-xs text-gray-500">Joined</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-gray-100 p-5">
        <h2 className="font-bold text-gray-900 mb-3">Order History</h2>
        <table className="w-full text-sm">
          <thead className="border-b">
            <tr>
              <th className="text-left pb-2 font-semibold text-gray-600">Order</th>
              <th className="text-left pb-2 font-semibold text-gray-600">Date</th>
              <th className="text-left pb-2 font-semibold text-gray-600">Status</th>
              <th className="text-right pb-2 font-semibold text-gray-600">Amount</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {orders.map((order) => (
              <tr key={order.id}>
                <td className="py-2.5">
                  <Link to={`/admin/orders/${order.id}`} className="font-medium text-teal-700 hover:text-teal-900">
                    #{order.orderNumber}
                  </Link>
                </td>
                <td className="py-2.5 text-gray-500">{formatDate(order.createdAt)}</td>
                <td className="py-2.5">{order.status}</td>
                <td className="py-2.5 text-right font-semibold">{formatINR(order.total)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default CustomerDetail;
