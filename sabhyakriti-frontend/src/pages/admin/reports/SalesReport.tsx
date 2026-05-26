import { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import type { SalesReport as SalesReportType } from '@/types';
import { getSalesReport } from '@/services/adminService';
import { formatINR, formatINRCompact } from '@/utils/currency';
import { formatDateInput } from '@/utils/date';
import LoadingSpinner from '@/components/shared/LoadingSpinner';

const today = new Date();
const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);

const SalesReport: React.FC = () => {
  const [report, setReport] = useState<SalesReportType | null>(null);
  const [loading, setLoading] = useState(false);
  const [from, setFrom] = useState(formatDateInput(thirtyDaysAgo.toISOString()));
  const [to, setTo] = useState(formatDateInput(today.toISOString()));

  const fetchReport = async () => {
    setLoading(true);
    try {
      const data = await getSalesReport(from, to);
      setReport(data);
    } catch {
      // handle error gracefully
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchReport(); }, []);

  return (
    <div data-testid="sales-report">
      <h1 className="text-xl font-bold text-gray-900 mb-6">Sales Report</h1>

      {/* Date range picker */}
      <div className="flex items-center gap-3 mb-6 flex-wrap">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">From:</label>
          <input type="date" value={from} onChange={(e) => setFrom(e.target.value)} data-testid="report-from-date" className="input-field text-sm w-36" />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">To:</label>
          <input type="date" value={to} onChange={(e) => setTo(e.target.value)} data-testid="report-to-date" className="input-field text-sm w-36" />
        </div>
        <button
          onClick={fetchReport}
          disabled={loading}
          data-testid="generate-report-btn"
          className="btn-primary text-sm py-2 px-4"
        >
          {loading ? 'Loading...' : 'Generate'}
        </button>
      </div>

      {loading && <div className="flex justify-center py-16"><LoadingSpinner size="lg" /></div>}

      {report && !loading && (
        <div className="space-y-6">
          {/* Summary KPIs */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {[
              { label: 'Total Revenue', value: formatINR(report.totalRevenue) },
              { label: 'Total Orders', value: report.totalOrders.toLocaleString() },
              { label: 'Avg Revenue/Day', value: formatINR(report.totalRevenue / Math.max(report.dataPoints.length, 1)) },
            ].map(({ label, value }) => (
              <div key={label} className="bg-white rounded-2xl border border-gray-100 p-4">
                <p className="text-2xl font-bold text-gray-900">{value}</p>
                <p className="text-sm text-gray-500 mt-0.5">{label}</p>
              </div>
            ))}
          </div>

          {/* Revenue Bar Chart */}
          <div className="bg-white rounded-2xl border border-gray-100 p-5">
            <h2 className="font-bold text-gray-800 mb-4">Revenue by Day</h2>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={report.dataPoints} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(val) => val.slice(5)} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(val) => formatINRCompact(val)} />
                <Tooltip formatter={(val) => formatINR(Number(val))} labelStyle={{ fontWeight: 600 }} />
                <Bar dataKey="revenue" fill="#FF6B2B" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Orders Line Chart */}
          <div className="bg-white rounded-2xl border border-gray-100 p-5">
            <h2 className="font-bold text-gray-800 mb-4">Orders Over Time</h2>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={report.dataPoints}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(val) => val.slice(5)} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="orders" stroke="#1B4B5A" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Top Products */}
          <div className="bg-white rounded-2xl border border-gray-100 p-5">
            <h2 className="font-bold text-gray-800 mb-3">Top Products</h2>
            <table className="w-full text-sm">
              <thead className="border-b">
                <tr>
                  <th className="text-left pb-2 font-semibold text-gray-600">Product</th>
                  <th className="text-right pb-2 font-semibold text-gray-600">Units Sold</th>
                  <th className="text-right pb-2 font-semibold text-gray-600">Revenue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {report.topProducts.map((p) => (
                  <tr key={p.productId} data-testid="top-product-row">
                    <td className="py-2.5 font-medium">{p.name}</td>
                    <td className="py-2.5 text-right text-gray-600">{p.unitsSold}</td>
                    <td className="py-2.5 text-right font-semibold">{formatINR(p.revenue)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Category Breakdown */}
          {report.categoryBreakdown.length > 0 && (
            <div className="bg-white rounded-2xl border border-gray-100 p-5">
              <h2 className="font-bold text-gray-800 mb-3">Category Breakdown</h2>
              <table className="w-full text-sm">
                <thead className="border-b">
                  <tr>
                    <th className="text-left pb-2 font-semibold text-gray-600">Category</th>
                    <th className="text-right pb-2 font-semibold text-gray-600">Revenue</th>
                    <th className="text-right pb-2 font-semibold text-gray-600">Share</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {report.categoryBreakdown.map((cat) => (
                    <tr key={cat.categoryName} data-testid="category-breakdown-row">
                      <td className="py-2.5">{cat.categoryName}</td>
                      <td className="py-2.5 text-right font-semibold">{formatINR(cat.revenue)}</td>
                      <td className="py-2.5 text-right text-gray-500">{cat.percentage.toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SalesReport;
