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
      className="absolute right-0 top-full mt-2 w-80 bg-white rounded-xl shadow-xl border border-gray-100 z-50 animate-slide-up"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <h3 className="font-semibold text-gray-900 flex items-center gap-2">
          <ShoppingCart className="h-4 w-4" /> Cart ({items.length})
        </h3>
        <button
          onClick={onClose}
          data-testid="mini-cart-close"
          className="text-gray-400 hover:text-gray-600"
          aria-label="Close cart"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Items */}
      {displayItems.length === 0 ? (
        <div className="py-8 text-center text-sm text-gray-500">
          <ShoppingCart className="h-10 w-10 mx-auto mb-2 text-gray-300" />
          Your cart is empty
        </div>
      ) : (
        <ul className="divide-y divide-gray-50 max-h-64 overflow-y-auto">
          {displayItems.map((item) => {
            const img = item.product.images.find((i) => i.isPrimary) ?? item.product.images[0];
            return (
              <li key={item.id} className="flex gap-3 px-4 py-3" data-testid="mini-cart-item">
                <img
                  src={img?.url ?? '/placeholder.jpg'}
                  alt={item.product.name}
                  className="h-12 w-12 object-cover rounded-lg flex-shrink-0"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{item.product.name}</p>
                  <p className="text-xs text-gray-500">Qty: {item.quantity}</p>
                  <p className="text-sm font-semibold text-saffron-500">{formatINR(item.subtotal)}</p>
                </div>
              </li>
            );
          })}
        </ul>
      )}

      {/* Total */}
      {totals && (
        <div className="px-4 py-2 bg-gray-50 border-t border-gray-100">
          <div className="flex justify-between text-sm font-semibold text-gray-900">
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
          className="flex-1 text-center py-2 text-sm font-medium border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          View Cart
        </Link>
        <Link
          to="/checkout"
          onClick={onClose}
          data-testid="mini-cart-checkout"
          className="flex-1 text-center py-2 text-sm font-medium bg-saffron-500 text-white rounded-lg hover:bg-saffron-600 transition-colors"
        >
          Checkout
        </Link>
      </div>
    </div>
  );
};

export default MiniCart;
