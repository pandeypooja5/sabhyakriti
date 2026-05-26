import { Minus, Plus, Trash2 } from 'lucide-react';
import type { CartItem as CartItemType } from '@/types';
import { formatINR } from '@/utils/currency';
import { useCart } from '@/hooks/useCart';
import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';

interface CartItemProps {
  item: CartItemType;
}

const CartItemComponent: React.FC<CartItemProps> = ({ item }) => {
  const { updateItem, removeItem } = useCart();
  const primaryImage = item.product.images.find((i) => i.isPrimary) ?? item.product.images[0];

  const handleQuantityChange = async (delta: number) => {
    const newQty = item.quantity + delta;
    if (newQty < 1) return;
    if (newQty > 10) return;
    await updateItem(item.id, newQty);
  };

  const handleRemove = async () => {
    await removeItem(item.id);
  };

  return (
    <div className="flex gap-4 py-4 border-b border-gray-100 last:border-0" data-testid="cart-item">
      {/* Image */}
      <Link to={`/sarees/${item.product.slug}`} className="flex-shrink-0">
        <img
          src={primaryImage?.url ?? '/placeholder.jpg'}
          alt={item.product.name}
          className="h-24 w-20 object-cover rounded-lg"
          data-testid="cart-item-image"
        />
      </Link>

      {/* Details */}
      <div className="flex-1 min-w-0">
        <Link
          to={`/sarees/${item.product.slug}`}
          className="text-sm font-medium text-gray-900 hover:text-saffron-500 line-clamp-2"
          data-testid="cart-item-name"
        >
          {item.product.name}
        </Link>
        <p className="text-xs text-gray-500 mt-0.5">{item.product.sku}</p>

        <div className="flex items-center justify-between mt-3">
          {/* Qty stepper */}
          <div className="flex items-center border border-gray-200 rounded-lg overflow-hidden">
            <button
              onClick={() => handleQuantityChange(-1)}
              disabled={item.quantity <= 1}
              data-testid="cart-item-decrease"
              className={cn(
                'h-7 w-7 flex items-center justify-center hover:bg-gray-50 transition-colors',
                item.quantity <= 1 && 'opacity-40 cursor-not-allowed'
              )}
              aria-label="Decrease quantity"
            >
              <Minus className="h-3 w-3" />
            </button>
            <span className="h-7 w-8 flex items-center justify-center text-sm font-medium border-x border-gray-200" data-testid="cart-item-qty">
              {item.quantity}
            </span>
            <button
              onClick={() => handleQuantityChange(1)}
              disabled={item.quantity >= 10}
              data-testid="cart-item-increase"
              className={cn(
                'h-7 w-7 flex items-center justify-center hover:bg-gray-50 transition-colors',
                item.quantity >= 10 && 'opacity-40 cursor-not-allowed'
              )}
              aria-label="Increase quantity"
            >
              <Plus className="h-3 w-3" />
            </button>
          </div>

          {/* Price */}
          <span className="font-bold text-gray-900 text-sm" data-testid="cart-item-subtotal">
            {formatINR(item.subtotal)}
          </span>
        </div>
      </div>

      {/* Remove */}
      <button
        onClick={handleRemove}
        data-testid="cart-item-remove"
        className="self-start text-gray-400 hover:text-red-500 transition-colors p-1"
        aria-label="Remove item"
      >
        <Trash2 className="h-4 w-4" />
      </button>
    </div>
  );
};

export default CartItemComponent;
