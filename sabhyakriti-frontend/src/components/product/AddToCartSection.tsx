import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Minus, Plus, ShoppingCart, Zap, Heart, Ruler } from 'lucide-react';
import type { Product } from '@/types';
import { useCart } from '@/hooks/useCart';
import { useWishlist } from '@/hooks/useWishlist';
import { useAuth } from '@/hooks/useAuth';
import { useAppDispatch } from '@/store/store';
import { openSizeGuide } from '@/store/slices/uiSlice';
import { cn } from '@/lib/utils';
import toast from 'react-hot-toast';

interface AddToCartSectionProps {
  product: Product;
}

const AddToCartSection: React.FC<AddToCartSectionProps> = ({ product }) => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [qty, setQty] = useState(1);
  const [addingToCart, setAddingToCart] = useState(false);

  const { addItem } = useCart();
  const { isWishlisted, toggle } = useWishlist();
  const { isAuthenticated } = useAuth();
  const wishlisted = isWishlisted(product.id);
  const outOfStock = product.stockStatus === 'OUT_OF_STOCK';

  const handleAddToCart = async () => {
    if (!isAuthenticated) {
      toast.error('Please login to add items to cart');
      navigate('/login');
      return;
    }
    setAddingToCart(true);
    try {
      await addItem(product.id, qty);
      toast.success(`${product.name} added to cart!`);
    } catch {
      toast.error('Failed to add to cart');
    } finally {
      setAddingToCart(false);
    }
  };

  const handleBuyNow = async () => {
    await handleAddToCart();
    navigate('/checkout');
  };

  const handleWishlist = async () => {
    if (!isAuthenticated) {
      toast.error('Please login to save to wishlist');
      return;
    }
    await toggle(product.id);
    toast.success(wishlisted ? 'Removed from wishlist' : 'Saved to wishlist');
  };

  return (
    <div className="space-y-4" data-testid="add-to-cart-section">
      {/* Quantity stepper */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-brand-text font-medium">Quantity:</span>
        <div className="flex items-center border border-ivory-500 rounded overflow-hidden">
          <button
            onClick={() => setQty((q) => Math.max(1, q - 1))}
            disabled={qty <= 1}
            data-testid="qty-decrease"
            className="h-9 w-9 flex items-center justify-center hover:bg-ivory-200 disabled:opacity-40 transition-colors"
            aria-label="Decrease quantity"
          >
            <Minus className="h-4 w-4" />
          </button>
          <span
            className="h-9 w-10 flex items-center justify-center text-sm font-semibold border-x border-ivory-500"
            data-testid="qty-display"
          >
            {qty}
          </span>
          <button
            onClick={() => setQty((q) => Math.min(10, q + 1))}
            disabled={qty >= 10 || qty >= product.stockQuantity}
            data-testid="qty-increase"
            className="h-9 w-9 flex items-center justify-center hover:bg-ivory-200 disabled:opacity-40 transition-colors"
            aria-label="Increase quantity"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>
        {product.stockQuantity <= 5 && product.stockStatus !== 'OUT_OF_STOCK' && (
          <span className="text-xs text-gold-700 font-medium">Only {product.stockQuantity} left!</span>
        )}
      </div>

      {/* Action buttons */}
      <div className="flex gap-3">
        <button
          onClick={handleAddToCart}
          disabled={outOfStock || addingToCart}
          data-testid="add-to-cart-btn"
          className={cn(
            'flex-1 flex items-center justify-center gap-2 py-3 rounded font-semibold text-sm transition-all',
            outOfStock || addingToCart
              ? 'bg-ivory-200 text-brand-textMuted cursor-not-allowed'
              : 'bg-saffron-500 hover:bg-saffron-600 text-white shadow-md hover:shadow-lg'
          )}
        >
          <ShoppingCart className="h-4 w-4" />
          {addingToCart ? 'Adding...' : outOfStock ? 'Out of Stock' : 'Add to Cart'}
        </button>

        <button
          onClick={handleBuyNow}
          disabled={outOfStock}
          data-testid="buy-now-btn"
          className={cn(
            'flex-1 flex items-center justify-center gap-2 py-3 rounded font-semibold text-sm transition-all border-2',
            outOfStock
              ? 'border-ivory-400 text-brand-textMuted cursor-not-allowed'
              : 'border-gold-600 text-gold-600 hover:bg-gold-50'
          )}
        >
          <Zap className="h-4 w-4" />
          Buy Now
        </button>
      </div>

      {/* Secondary actions */}
      <div className="flex gap-3">
        <button
          onClick={handleWishlist}
          data-testid="wishlist-toggle-btn"
          className={cn(
            'flex-1 flex items-center justify-center gap-2 py-2.5 rounded text-sm font-medium border transition-colors',
            wishlisted
              ? 'border-burgundy-300 bg-burgundy-50 text-burgundy-600'
              : 'border-ivory-400 text-brand-textMuted hover:border-ivory-500'
          )}
        >
          <Heart className={cn('h-4 w-4', wishlisted && 'fill-current text-burgundy-500')} />
          {wishlisted ? 'Wishlisted' : 'Wishlist'}
        </button>

        <button
          onClick={() => dispatch(openSizeGuide())}
          data-testid="size-guide-btn"
          className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded text-sm font-medium border border-ivory-400 text-brand-textMuted hover:border-ivory-500 transition-colors"
        >
          <Ruler className="h-4 w-4" />
          Size Guide
        </button>
      </div>
    </div>
  );
};

export default AddToCartSection;
