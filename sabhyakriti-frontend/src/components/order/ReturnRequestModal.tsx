import { useState } from 'react';
import { X, RotateCcw } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '@/store/store';
import { closeReturnModal } from '@/store/slices/uiSlice';
import { submitReturn } from '@/services/orderService';
import { useAppSelector as useSelector } from '@/store/store';
import toast from 'react-hot-toast';

const returnReasons = [
  'Wrong product delivered',
  'Product damaged',
  'Quality not as expected',
  'Size/fit issue',
  'Color different from images',
  'Other',
];

const ReturnRequestModal: React.FC = () => {
  const dispatch = useAppDispatch();
  const { open, orderId } = useAppSelector((s) => s.ui.modals.returnRequest);
  const currentOrder = useSelector((s) => s.orders.currentOrder);

  const [selectedItems, setSelectedItems] = useState<Record<string, { qty: number; reason: string }>>({});
  const [submitting, setSubmitting] = useState(false);

  if (!open || !orderId) return null;

  const orderItems = currentOrder?.items ?? [];

  const toggleItem = (itemId: string) => {
    setSelectedItems((prev) => {
      if (prev[itemId]) {
        const next = { ...prev };
        delete next[itemId];
        return next;
      }
      return { ...prev, [itemId]: { qty: 1, reason: '' } };
    });
  };

  const handleSubmit = async () => {
    const items = Object.entries(selectedItems).map(([orderItemId, data]) => ({
      orderItemId,
      quantity: data.qty,
      reason: data.reason,
    }));
    if (items.length === 0) { toast.error('Select at least one item'); return; }
    if (items.some((i) => !i.reason)) { toast.error('Please select a reason for each item'); return; }

    setSubmitting(true);
    try {
      await submitReturn({ orderId, items });
      toast.success('Return request submitted!');
      dispatch(closeReturnModal());
    } catch {
      toast.error('Failed to submit return request');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" data-testid="return-request-modal">
      <div className="absolute inset-0 bg-black/50" onClick={() => dispatch(closeReturnModal())} />
      <div className="relative bg-white rounded-2xl w-full max-w-lg shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-100 p-4 flex items-center justify-between">
          <h2 className="font-bold text-gray-900 flex items-center gap-2">
            <RotateCcw className="h-5 w-5 text-saffron-500" /> Return Request
          </h2>
          <button
            onClick={() => dispatch(closeReturnModal())}
            data-testid="return-modal-close"
            className="text-gray-400 hover:text-gray-600"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-4 space-y-4">
          <p className="text-sm text-gray-600">Select items to return:</p>

          {orderItems.map((item) => {
            const isSelected = !!selectedItems[item.id];
            return (
              <div key={item.id} className="border rounded-xl p-3" data-testid={`return-item-${item.id}`}>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleItem(item.id)}
                    className="h-4 w-4 text-saffron-500 rounded focus:ring-saffron-500"
                  />
                  <img
                    src={item.product.images[0]?.url}
                    alt={item.product.name}
                    className="h-12 w-10 object-cover rounded"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{item.product.name}</p>
                    <p className="text-xs text-gray-500">Qty: {item.quantity}</p>
                  </div>
                </label>

                {isSelected && (
                  <div className="mt-3 space-y-2 pl-7">
                    <div className="flex items-center gap-2">
                      <label className="text-xs text-gray-600">Return qty:</label>
                      <select
                        value={selectedItems[item.id].qty}
                        onChange={(e) => setSelectedItems((prev) => ({ ...prev, [item.id]: { ...prev[item.id], qty: Number(e.target.value) } }))}
                        className="text-sm border border-gray-200 rounded px-1.5 py-1"
                      >
                        {Array.from({ length: item.quantity }, (_, i) => i + 1).map((n) => (
                          <option key={n} value={n}>{n}</option>
                        ))}
                      </select>
                    </div>
                    <select
                      value={selectedItems[item.id].reason}
                      onChange={(e) => setSelectedItems((prev) => ({ ...prev, [item.id]: { ...prev[item.id], reason: e.target.value } }))}
                      className="w-full text-sm border border-gray-200 rounded px-2 py-1.5"
                      data-testid={`return-reason-${item.id}`}
                    >
                      <option value="">Select reason *</option>
                      {returnReasons.map((r) => <option key={r} value={r}>{r}</option>)}
                    </select>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div className="sticky bottom-0 bg-white border-t border-gray-100 p-4 flex gap-3">
          <button
            onClick={() => dispatch(closeReturnModal())}
            className="flex-1 py-2.5 border border-gray-300 text-gray-700 font-medium rounded-xl"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting}
            data-testid="return-submit-btn"
            className="flex-1 py-2.5 bg-saffron-500 hover:bg-saffron-600 text-white font-semibold rounded-xl disabled:opacity-60"
          >
            {submitting ? 'Submitting...' : 'Submit Request'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReturnRequestModal;
