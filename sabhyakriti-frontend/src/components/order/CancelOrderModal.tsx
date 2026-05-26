import { useState } from 'react';
import { AlertTriangle, X } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '@/store/store';
import { closeCancelOrderModal } from '@/store/slices/uiSlice';
import { cancelOrder } from '@/store/slices/orderSlice';
import toast from 'react-hot-toast';

const cancelReasons = [
  'Changed my mind',
  'Found a better price',
  'Ordered by mistake',
  'Delivery time too long',
  'Payment issue',
  'Other',
];

const CancelOrderModal: React.FC = () => {
  const dispatch = useAppDispatch();
  const { open, orderId } = useAppSelector((s) => s.ui.modals.cancelOrder);
  const [reason, setReason] = useState('');
  const [customReason, setCustomReason] = useState('');
  const [loading, setLoading] = useState(false);

  if (!open || !orderId) return null;

  const handleCancel = async () => {
    const finalReason = reason === 'Other' ? customReason : reason;
    if (!finalReason.trim()) { toast.error('Please select a reason'); return; }

    setLoading(true);
    try {
      await dispatch(cancelOrder({ orderId, reason: finalReason })).unwrap();
      toast.success('Order cancelled successfully');
      dispatch(closeCancelOrderModal());
    } catch (err: unknown) {
      const error = err as string;
      toast.error(error || 'Failed to cancel order');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" data-testid="cancel-order-modal">
      <div className="absolute inset-0 bg-black/50" onClick={() => dispatch(closeCancelOrderModal())} />
      <div className="relative bg-white rounded-2xl w-full max-w-md shadow-2xl p-6">
        <button
          onClick={() => dispatch(closeCancelOrderModal())}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
          data-testid="cancel-modal-close"
          aria-label="Close"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="h-10 w-10 rounded-full bg-red-100 flex items-center justify-center">
            <AlertTriangle className="h-5 w-5 text-red-600" />
          </div>
          <h2 className="text-lg font-bold text-gray-900">Cancel Order</h2>
        </div>

        <p className="text-sm text-gray-600 mb-4">Please select a reason for cancellation:</p>

        <div className="space-y-2 mb-4">
          {cancelReasons.map((r) => (
            <label key={r} className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="cancel-reason"
                value={r}
                checked={reason === r}
                onChange={() => setReason(r)}
                data-testid={`cancel-reason-${r.toLowerCase().replace(/ /g, '-')}`}
                className="text-saffron-500 focus:ring-saffron-500"
              />
              <span className="text-sm text-gray-700">{r}</span>
            </label>
          ))}
        </div>

        {reason === 'Other' && (
          <textarea
            value={customReason}
            onChange={(e) => setCustomReason(e.target.value)}
            placeholder="Please specify your reason..."
            data-testid="cancel-reason-custom"
            rows={3}
            className="input-field mb-4 resize-none"
          />
        )}

        <div className="flex gap-3">
          <button
            onClick={() => dispatch(closeCancelOrderModal())}
            data-testid="cancel-modal-dismiss"
            className="flex-1 py-2.5 border border-gray-300 text-gray-700 font-medium rounded-xl hover:bg-gray-50"
          >
            Keep Order
          </button>
          <button
            onClick={handleCancel}
            disabled={loading}
            data-testid="cancel-order-confirm-btn"
            className="flex-1 py-2.5 bg-red-500 hover:bg-red-600 text-white font-semibold rounded-xl disabled:opacity-60 transition-colors"
          >
            {loading ? 'Cancelling...' : 'Cancel Order'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CancelOrderModal;
