import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { X, ShoppingCart } from 'lucide-react';
import { useCart } from '@/hooks/useCart';
import { formatINR } from '@/utils/currency';

interface MiniCartProps {
  onClose: () => void;
}

const MiniCart: React.FC<MiniCartProps> = ({ onClose }) => {
  const { items, totals, refetchCart } = useCart();

  useEffect(() => {
    refetchCart();
  }, [refetchCart]);

  const displayItems = items.slice(-3).reverse();

  return (
    <div
      data-testid="mini-cart"
      className="absolute right-0 top-full mt-2 w-80 bg-ivory-100 rounded shadow-xl border border-ivory-400 z-50 animate-slide-up"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-ivory-400">
        <h3 className="font-semibold text-brand-text flex items-center gap-2">
          <ShoppingCart className="h-4 w-4" /> Cart ({items.length})
        </h3>
        <button
          onClick={onClose}
          data-testid="mini-cart-close"
          className="text-brand-textMuted hover:text-brand-text"
          aria-label="Close cart"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Items */}
      {displayItems.length === 0 ? (
        <div className="py-8 text-center text-sm text-brand-textMuted">
          <ShoppingCart className="h-10 w-10 mx-auto mb-2 text-ivory-400" />
          Your cart is empty
        </div>
      ) : (
        <ul className="divide-y divide-ivory-200 max-h-64 overflow-y-auto">
          {displayItems.map((item) => {
            const img = item.product?.images?.find((i) => i.isPrimary) ?? item.product?.images?.[0];
            return (
              <li key={item.id} className="flex gap-3 px-4 py-3" data-testid="mini-cart-item">
                <img
                  src={img?.url ?? '/placeholder.jpg'}
                  alt={item.product?.name ?? 'Product'}
                  className="h-12 w-12 object-cover rounded-lg flex-shrink-0"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-brand-text truncate">{item.product?.name ?? 'Unknown Product'}</p>
                  <p className="text-xs text-brand-textMuted">Qty: {item.quantity}</p>
                  <p className="text-sm font-semibold text-gold-700">{formatINR(item.subtotal)}</p>
                </div>
              </li>
            );
          })}
        </ul>
      )}

      {/* Total */}
      {totals && (
        <div className="px-4 py-2 bg-ivory-200 border-t border-ivory-400">
          <div className="flex justify-between text-sm font-semibold text-brand-text">
            <span>Total</span>
            <span>{formatINR(totals.total)}</span>
          </div>
        </div>
      )}

      {/* CTAs */}
      <div className="flex gap-2 p-4">
        <Link
          to="/cart"
          onClick={onClose}
          data-testid="mini-cart-view"
          className="flex-1 text-center py-2 text-sm font-medium border border-ivory-500 text-brand-text rounded hover:bg-ivory-200 transition-colors"
        >
          View Cart
        </Link>
        <Link
          to="/checkout"
          onClick={onClose}
          data-testid="mini-cart-checkout"
          className="flex-1 text-center py-2 text-sm font-medium bg-gold-600 text-white rounded hover:bg-gold-700 transition-colors"
        >
          Checkout
        </Link>
      </div>
    </div>
  );
};

export default MiniCart;
