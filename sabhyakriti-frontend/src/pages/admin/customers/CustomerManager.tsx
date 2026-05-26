import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Eye } from 'lucide-react';
import type { User } from '@/types';
import { listCustomers } from '@/services/adminService';
import { formatDate } from '@/utils/date';
import LoadingSpinner from '@/components/shared/LoadingSpinner';

const CustomerManager: React.FC = () => {
  const [customers, setCustomers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    setLoading(true);
    listCustomers(page, search || undefined)
      .then((res) => { setCustomers(res.data); setTotal(res.total); })
      .catch(() => null)
      .finally(() => setLoading(false));
  }, [page, search]);

  return (
    <div data-testid="customer-manager">
      <h1 className="text-xl font-bold text-gray-900 mb-6">Customers ({total})</h1>

      <div className="relative max-w-xs mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} placeholder="Search by name/email..." data-testid="customer-search" className="input-field pl-9" />
      </div>

      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-16"><LoadingSpinner /></div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                {['Name', 'Email', 'Phone', 'Joined', 'Verified', 'Action'].map((h) => (
                  <th key={h} className="text-left px-4 py-3 font-semibold text-gray-600">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {customers.map((customer) => (
                <tr key={customer.id} className="hover:bg-gray-50" data-testid="customer-row">
                  <td className="px-4 py-3 font-medium text-gray-900">{customer.name}</td>
                  <td className="px-4 py-3 text-gray-600">{customer.email}</td>
                  <td className="px-4 py-3 text-gray-500">{customer.phone ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-500">{formatDate(customer.createdAt)}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${customer.isVerified ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                      {customer.isVerified ? 'Yes' : 'No'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <Link to={`/admin/customers/${customer.id}`} data-testid={`view-customer-${customer.id}`} className="p-1.5 text-teal-700 hover:bg-teal-50 rounded-lg inline-flex">
                      <Eye className="h-4 w-4" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {total > 20 && (
        <div className="flex justify-center gap-2 mt-4">
          <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)} className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-40">Prev</button>
          <button onClick={() => setPage((p) => p + 1)} className="px-3 py-1.5 text-sm border rounded-lg">Next</button>
        </div>
      )}
    </div>
  );
};

export default CustomerManager;
