import { useState } from 'react';
import { Tag, X, CheckCircle } from 'lucide-react';
import { useCart } from '@/hooks/useCart';
import { formatINR } from '@/utils/currency';
import toast from 'react-hot-toast';

const CouponInput: React.FC = () => {
  const { couponCode, totals, applyCode, removeCode, loading } = useCart();
  const [inputValue, setInputValue] = useState('');

  const handleApply = async () => {
    if (!inputValue.trim()) return;
    const result = await applyCode(inputValue.trim().toUpperCase());
    if ((result as { error?: boolean }).error) {
      toast.error('Invalid or expired coupon code');
    } else {
      toast.success('Coupon applied!');
      setInputValue('');
    }
  };

  const handleRemove = async () => {
    await removeCode();
    toast.success('Coupon removed');
  };

  if (couponCode) {
    return (
      <div
        className="flex items-center justify-between p-3 bg-green-50 rounded-xl border border-green-200"
        data-testid="coupon-applied"
      >
        <div className="flex items-center gap-2">
          <CheckCircle className="h-4 w-4 text-green-600 flex-shrink-0" />
          <div>
            <span className="text-sm font-semibold text-green-800">{couponCode}</span>
            {totals?.couponDiscount && totals.couponDiscount > 0 && (
              <p className="text-xs text-green-600">You save {formatINR(totals.couponDiscount)}</p>
            )}
          </div>
        </div>
        <button
          onClick={handleRemove}
          data-testid="coupon-remove-btn"
          className="text-green-600 hover:text-green-800 transition-colors"
          aria-label="Remove coupon"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    );
  }

  return (
    <div className="flex gap-2" data-testid="coupon-input">
      <div className="relative flex-1">
        <Tag className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === 'Enter' && handleApply()}
          placeholder="Enter coupon code"
          data-testid="coupon-code-input"
          className="w-full pl-9 pr-3 py-2.5 text-sm border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-saffron-500 focus:border-transparent uppercase placeholder-normal"
        />
      </div>
      <button
        onClick={handleApply}
        disabled={!inputValue.trim() || loading}
        data-testid="coupon-apply-btn"
        className="px-4 py-2.5 bg-teal-700 text-white text-sm font-medium rounded-xl hover:bg-teal-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        Apply
      </button>
    </div>
  );
};

export default CouponInput;
