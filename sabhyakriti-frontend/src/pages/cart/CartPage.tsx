import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ShoppingBag } from 'lucide-react';
import { useCart } from '@/hooks/useCart';
import CartItemComponent from '@/components/cart/CartItem';
import CartSummary from '@/components/cart/CartSummary';
import EmptyState from '@/components/shared/EmptyState';
import LoadingSpinner from '@/components/shared/LoadingSpinner';
import Breadcrumb from '@/components/shared/Breadcrumb';

const CartPage: React.FC = () => {
  const { items, loading, refetchCart } = useCart();

  useEffect(() => {
    refetchCart();
  }, [refetchCart]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6" data-testid="cart-page">
      <Breadcrumb items={[{ label: 'Shopping Cart' }]} />
      <h1 className="text-2xl font-bold text-gray-900 mt-4 mb-6 flex items-center gap-2">
        <ShoppingBag className="h-6 w-6" />
        Shopping Cart
        {items.length > 0 && (
          <span className="text-base font-normal text-gray-500">({items.length} items)</span>
        )}
      </h1>

      {loading ? (
        <div className="flex justify-center py-20"><LoadingSpinner size="lg" /></div>
      ) : items.length === 0 ? (
        <EmptyState
          icon={<ShoppingBag className="h-16 w-16" />}
          title="Your cart is empty"
          message="Discover our beautiful collection of handcrafted sarees."
          ctaLabel="Browse Sarees"
          ctaHref="/sarees"
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Cart Items */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl border border-gray-100 p-4">
              {items.map((item) => (
                <CartItemComponent key={item.id} item={item} />
              ))}
            </div>
            <div className="mt-4">
              <Link
                to="/sarees"
                data-testid="continue-shopping"
                className="text-sm text-saffron-500 hover:text-saffron-600 font-medium"
              >
                ← Continue Shopping
              </Link>
            </div>
          </div>

          {/* Summary */}
          <div>
            <CartSummary />
          </div>
        </div>
      )}
    </div>
  );
};

export default CartPage;
