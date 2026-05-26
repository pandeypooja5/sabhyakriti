import { useEffect, useState } from 'react';
import { Heart } from 'lucide-react';
import type { WishlistItem } from '@/types';
import { getWishlist, removeFromWishlist } from '@/services/wishlistService';
import { clearWishlist } from '@/store/slices/wishlistSlice';
import { useAppDispatch } from '@/store/store';
import ProductCard from '@/components/product/ProductCard';
import EmptyState from '@/components/shared/EmptyState';
import LoadingSpinner from '@/components/shared/LoadingSpinner';
import toast from 'react-hot-toast';

const WishlistPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const [items, setItems] = useState<WishlistItem[]>([]);
  const [loading, setLoading] = useState(true);

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

  if (loading) return <div className="flex justify-center py-12"><LoadingSpinner /></div>;

  return (
    <div data-testid="wishlist-page">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-bold text-gray-900 flex items-center gap-2">
          <Heart className="h-5 w-5 text-saffron-500" /> My Wishlist
          {items.length > 0 && <span className="text-sm font-normal text-gray-500">({items.length} items)</span>}
        </h2>
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
            <div key={item.id} className="relative">
              <ProductCard product={item.product} />
              <button
                onClick={() => handleRemove(item.productId)}
                data-testid={`remove-wishlist-${item.productId}`}
                className="absolute top-2 right-2 h-7 w-7 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 text-xs font-bold"
                aria-label="Remove from wishlist"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default WishlistPage;
