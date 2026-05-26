import { useState } from 'react';
import { CreditCard, Smartphone, Truck } from 'lucide-react';
import type { PaymentMethod } from '@/types';
import { cn } from '@/lib/utils';

interface PaymentStepProps {
  onNext: (method: PaymentMethod) => void;
  onBack: () => void;
}

const paymentOptions: { method: PaymentMethod; label: string; desc: string; Icon: React.FC<{ className?: string }> }[] = [
  { method: 'RAZORPAY', label: 'Card / Net Banking / UPI', desc: 'Pay securely via Razorpay', Icon: CreditCard },
  { method: 'UPI', label: 'UPI (Direct)', desc: 'Pay directly via UPI ID', Icon: Smartphone },
  { method: 'COD', label: 'Cash on Delivery', desc: 'Pay when your order arrives', Icon: Truck },
];

const PaymentStep: React.FC<PaymentStepProps> = ({ onNext, onBack }) => {
  const [selected, setSelected] = useState<PaymentMethod>('RAZORPAY');
  const [upiId, setUpiId] = useState('');

  const handleContinue = () => {
    onNext(selected);
  };

  return (
    <div data-testid="payment-step">
      <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
        <CreditCard className="h-5 w-5 text-saffron-500" /> Payment Method
      </h2>

      <div className="space-y-3 mb-6">
        {paymentOptions.map(({ method, label, desc, Icon }) => (
          <label
            key={method}
            className={cn(
              'flex items-center gap-3 p-4 rounded-xl border-2 cursor-pointer transition-colors',
              selected === method ? 'border-saffron-500 bg-saffron-50' : 'border-gray-200 hover:border-gray-300'
            )}
            data-testid={`payment-option-${method.toLowerCase()}`}
          >
            <input
              type="radio"
              name="payment"
              value={method}
              checked={selected === method}
              onChange={() => setSelected(method)}
              className="text-saffron-500 focus:ring-saffron-500"
            />
            <Icon className="h-5 w-5 text-teal-700 flex-shrink-0" />
            <div>
              <p className="text-sm font-semibold text-gray-900">{label}</p>
              <p className="text-xs text-gray-500">{desc}</p>
            </div>
          </label>
        ))}
      </div>

      {/* UPI input if selected */}
      {selected === 'UPI' && (
        <div className="mb-4">
          <label className="text-sm font-medium text-gray-700 mb-1 block">UPI ID</label>
          <input
            type="text"
            value={upiId}
            onChange={(e) => setUpiId(e.target.value)}
            placeholder="yourname@upi"
            data-testid="upi-id-input"
            className="input-field"
          />
        </div>
      )}

      {/* COD notice */}
      {selected === 'COD' && (
        <div className="mb-4 p-3 bg-amber-50 rounded-xl border border-amber-200">
          <p className="text-sm text-amber-800">
            Cash on Delivery is available. Extra ₹50 handling fee may apply for COD orders.
          </p>
        </div>
      )}

      <div className="flex gap-3">
        <button
          onClick={onBack}
          data-testid="payment-back-btn"
          className="flex-1 py-3 border border-gray-300 text-gray-700 font-medium rounded-xl hover:bg-gray-50 transition-colors"
        >
          Back
        </button>
        <button
          onClick={handleContinue}
          data-testid="payment-continue-btn"
          className="flex-1 py-3 bg-saffron-500 hover:bg-saffron-600 text-white font-semibold rounded-xl transition-colors"
        >
          Review Order
        </button>
      </div>
    </div>
  );
};

export default PaymentStep;
