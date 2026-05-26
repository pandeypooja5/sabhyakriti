import { useEffect, useState } from 'react';
import { CheckCircle, XCircle } from 'lucide-react';
import type { ReturnRequest } from '@/types';
import { listReturns, processReturn } from '@/services/adminService';
import { formatDate } from '@/utils/date';
import { formatINR } from '@/utils/currency';
import LoadingSpinner from '@/components/shared/LoadingSpinner';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';

const statusColors: Record<string, string> = {
  PENDING: 'bg-amber-100 text-amber-700',
  APPROVED: 'bg-green-100 text-green-700',
  REJECTED: 'bg-red-100 text-red-700',
  COMPLETED: 'bg-gray-100 text-gray-700',
};

const ReturnManager: React.FC = () => {
  const [returns, setReturns] = useState<ReturnRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('PENDING');
  const [processing, setProcessing] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    listReturns(statusFilter || undefined)
      .then((res) => setReturns(res.data))
      .catch(() => null)
      .finally(() => setLoading(false));
  }, [statusFilter]);

  const handleProcess = async (returnId: string, action: 'APPROVE' | 'REJECT', note?: string) => {
    setProcessing(returnId);
    try {
      const updated = await processReturn(returnId, action, note);
      setReturns((prev) => prev.map((r) => r.id === returnId ? updated : r));
      toast.success(`Return ${action.toLowerCase()}d`);
    } catch {
      toast.error('Failed to process return');
    } finally {
      setProcessing(null);
    }
  };

  return (
    <div data-testid="return-manager">
      <h1 className="text-xl font-bold text-gray-900 mb-6">Return Requests</h1>

      <div className="flex gap-2 mb-4">
        {['PENDING', 'APPROVED', 'REJECTED', 'COMPLETED', ''].map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            data-testid={`return-filter-${s || 'all'}`}
            className={cn('px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap', statusFilter === s ? 'bg-teal-700 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200')}
          >
            {s || 'All'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-16"><LoadingSpinner /></div>
      ) : returns.length === 0 ? (
        <div className="text-center py-16 text-gray-500">No return requests found</div>
      ) : (
        <div className="space-y-4">
          {returns.map((ret) => (
            <div key={ret.id} className="bg-white rounded-2xl border border-gray-100 p-5" data-testid="return-row">
              <div className="flex items-start justify-between gap-4 mb-3">
                <div>
                  <p className="font-semibold text-gray-900">Return #{ret.id.slice(-8).toUpperCase()}</p>
                  <p className="text-sm text-gray-500">
                    Order #{ret.order?.orderNumber} · {formatDate(ret.createdAt)}
                  </p>
                </div>
                <span className={cn('px-2.5 py-0.5 rounded-full text-xs font-medium', statusColors[ret.status] ?? 'bg-gray-100 text-gray-700')}>
                  {ret.status}
                </span>
              </div>

              <div className="space-y-1 mb-3">
                {ret.items.map((item, idx) => (
                  <p key={idx} className="text-sm text-gray-600">
                    Qty {item.quantity} — {item.reason}
                  </p>
                ))}
              </div>

              {ret.refundAmount && (
                <p className="text-sm font-semibold text-green-700 mb-3">
                  Refund: {formatINR(ret.refundAmount)}
                </p>
              )}

              {ret.status === 'PENDING' && (
                <div className="flex gap-2">
                  <button
                    onClick={() => handleProcess(ret.id, 'APPROVE')}
                    disabled={processing === ret.id}
                    data-testid={`approve-return-${ret.id}`}
                    className="flex items-center gap-1.5 px-3 py-2 bg-green-600 text-white text-sm font-medium rounded-xl hover:bg-green-700 disabled:opacity-50"
                  >
                    <CheckCircle className="h-4 w-4" /> Approve
                  </button>
                  <button
                    onClick={() => handleProcess(ret.id, 'REJECT', 'Does not meet return criteria')}
                    disabled={processing === ret.id}
                    data-testid={`reject-return-${ret.id}`}
                    className="flex items-center gap-1.5 px-3 py-2 border border-red-300 text-red-600 text-sm font-medium rounded-xl hover:bg-red-50 disabled:opacity-50"
                  >
                    <XCircle className="h-4 w-4" /> Reject
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ReturnManager;
