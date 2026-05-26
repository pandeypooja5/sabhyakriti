import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, ShoppingBag, Users, Package, RotateCcw, DollarSign, Activity, ArrowUpRight } from 'lucide-react';
import { getDashboard } from '@/services/adminService';
import type { DashboardKPIs, Order } from '@/types';
import { formatINR, formatINRCompact } from '@/utils/currency';
import { formatDate } from '@/utils/date';
import LoadingSpinner from '@/components/shared/LoadingSpinner';
import { cn } from '@/lib/utils';

interface KPICardProps {
  title: string;
  value: string;
  growth?: number;
  Icon: React.FC<{ className?: string }>;
  color: string;
}

const KPICard: React.FC<KPICardProps> = ({ title, value, growth, Icon, color }) => (
  <div className="bg-white rounded-2xl border border-gray-100 p-5" data-testid="kpi-card">
    <div className="flex items-center justify-between mb-3">
      <div className={cn('h-10 w-10 rounded-xl flex items-center justify-center', color)}>
        <Icon className="h-5 w-5 text-white" />
      </div>
      {growth !== undefined && (
        <span className={cn('flex items-center gap-0.5 text-xs font-medium', growth >= 0 ? 'text-green-600' : 'text-red-500')}>
          <ArrowUpRight className={cn('h-3 w-3', growth < 0 && 'rotate-180')} />
          {Math.abs(growth)}%
        </span>
      )}
    </div>
    <p className="text-2xl font-bold text-gray-900">{value}</p>
    <p className="text-sm text-gray-500 mt-0.5">{title}</p>
  </div>
);

const AdminDashboard: React.FC = () => {
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);
  const [recentOrders, setRecentOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboard()
      .then((data) => { setKpis(data.kpis); setRecentOrders(data.recentOrders); })
      .catch(() => null)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-20"><LoadingSpinner size="lg" /></div>;

  const cards: KPICardProps[] = kpis ? [
    { title: 'Total Revenue', value: formatINRCompact(kpis.totalRevenue), growth: kpis.revenueGrowth, Icon: DollarSign, color: 'bg-saffron-500' },
    { title: 'Total Orders', value: kpis.totalOrders.toLocaleString(), growth: kpis.orderGrowth, Icon: ShoppingBag, color: 'bg-teal-700' },
    { title: 'Customers', value: kpis.totalCustomers.toLocaleString(), Icon: Users, color: 'bg-blue-600' },
    { title: 'Products', value: kpis.totalProducts.toLocaleString(), Icon: Package, color: 'bg-purple-600' },
    { title: 'Avg Order Value', value: formatINR(kpis.averageOrderValue), Icon: TrendingUp, color: 'bg-emerald-600' },
    { title: 'Pending Returns', value: kpis.pendingReturns.toLocaleString(), Icon: RotateCcw, color: 'bg-orange-500' },
  ] : [];

  return (
    <div data-testid="admin-dashboard">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Dashboard</h1>
        <Link to="/admin/reports" className="text-sm font-medium text-saffron-500 flex items-center gap-1">
          <Activity className="h-4 w-4" /> View Reports
        </Link>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {cards.map((card) => <KPICard key={card.title} {...card} />)}
      </div>

      {/* Recent orders */}
      <div className="bg-white rounded-2xl border border-gray-100 p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-bold text-gray-900">Recent Orders</h2>
          <Link to="/admin/orders" className="text-sm text-saffron-500 font-medium">View All</Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b border-gray-100">
                <th className="pb-2 font-medium">Order</th>
                <th className="pb-2 font-medium">Customer</th>
                <th className="pb-2 font-medium">Date</th>
                <th className="pb-2 font-medium">Status</th>
                <th className="pb-2 font-medium text-right">Amount</th>
              </tr>
            </thead>
            <tbody>
              {recentOrders.map((order) => (
                <tr key={order.id} className="border-b border-gray-50 hover:bg-gray-50" data-testid="dashboard-order-row">
                  <td className="py-2.5">
                    <Link to={`/admin/orders/${order.id}`} className="font-medium text-teal-700 hover:text-teal-900">
                      #{order.orderNumber}
                    </Link>
                  </td>
                  <td className="py-2.5 text-gray-700">{order.shippingAddress.name}</td>
                  <td className="py-2.5 text-gray-500">{formatDate(order.createdAt)}</td>
                  <td className="py-2.5">
                    <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                      {order.status}
                    </span>
                  </td>
                  <td className="py-2.5 text-right font-semibold">{formatINR(order.total)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
