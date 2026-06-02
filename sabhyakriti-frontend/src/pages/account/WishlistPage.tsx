import { useEffect, useState } from 'react';
import { Heart, ShoppingCart } from 'lucide-react';
import type { WishlistItem } from '@/types';
import { getWishlist, removeFromWishlist } from '@/services/wishlistService';
import { clearWishlist } from '@/store/slices/wishlistSlice';
import { useAppDispatch } from '@/store/store';
import { useCart } from '@/hooks/useCart';
import ProductCard from '@/components/product/ProductCard';
import EmptyState from '@/components/shared/EmptyState';
import LoadingSpinner from '@/components/shared/LoadingSpinner';
import Breadcrumb from '@/components/shared/Breadcrumb';
import toast from 'react-hot-toast';

const WishlistPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { addItem, refetchCart } = useCart();
  const [items, setItems] = useState<WishlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [movingId, setMovingId] = useState<string | null>(null);

  useEffect(() => {
    getWishlist()
      .then(setItems)
      .catch(() => null)
      .finally(() => setLoading(false));
  }, []);

  const handleRemove = async (productId: string) => {
    try {
      await removeFromWishlist(productId);
      setItems((prev) => prev.filter((i) => i.productId !== productId));
      toast.success('Removed from wishlist');
    } catch {
      toast.error('Failed to remove from wishlist');
    }
  };

  const handleMoveToCart = async (productId: string) => {
    setMovingId(productId);
    try {
      const result = await addItem(productId, 1);
      // addItem is a thunk; check if it rejected
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      if ((result as any)?.error) throw new Error('add failed');
      await removeFromWishlist(productId);
      setItems((prev) => prev.filter((i) => i.productId !== productId));
      await refetchCart();
      toast.success('Moved to cart');
    } catch {
      toast.error('Could not move to cart');
    } finally {
      setMovingId(null);
    }
  };

  if (loading) return <div className="flex justify-center py-12"><LoadingSpinner /></div>;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6" data-testid="wishlist-page">
      <Breadcrumb items={[{ label: 'My Wishlist' }]} />
      <div className="flex items-center justify-between mt-4 mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Heart className="h-6 w-6 text-saffron-500" /> My Wishlist
          {items.length > 0 && <span className="text-base font-normal text-gray-500">({items.length} items)</span>}
        </h1>
        {items.length > 0 && (
          <button
            onClick={() => { dispatch(clearWishlist()); setItems([]); }}
            data-testid="clear-wishlist-btn"
            className="text-xs text-red-500 hover:text-red-700 font-medium"
          >
            Clear All
          </button>
        )}
      </div>

      {items.length === 0 ? (
        <EmptyState
          icon={<Heart className="h-16 w-16" />}
          title="Your wishlist is empty"
          message="Save sarees you love and come back to them later."
          ctaLabel="Browse Sarees"
          ctaHref="/sarees"
        />
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {items.map((item) => (
            <div key={item.id} className="relative flex flex-col">
              <ProductCard product={item.product} />
              <button
                onClick={() => handleRemove(item.productId)}
                data-testid={`remove-wishlist-${item.productId}`}
                className="absolute top-2 right-2 h-7 w-7 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 text-xs font-bold z-10"
                aria-label="Remove from wishlist"
              >
                ×
              </button>
              <button
                onClick={() => handleMoveToCart(item.productId)}
                disabled={movingId === item.productId}
                data-testid={`move-to-cart-${item.productId}`}
                className="mt-2 flex items-center justify-center gap-2 w-full bg-saffron-500 hover:bg-saffron-600 text-white text-sm font-semibold py-2 rounded-lg transition-colors disabled:opacity-60"
              >
                <ShoppingCart className="h-4 w-4" />
                {movingId === item.productId ? 'Moving…' : 'Move to Cart'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default WishlistPage;
