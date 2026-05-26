import type { Product } from '@/types';
import ProductCard from './ProductCard';
import LoadingSpinner from '@/components/shared/LoadingSpinner';
import EmptyState from '@/components/shared/EmptyState';
import { Search } from 'lucide-react';

interface ProductGridProps {
  products: Product[];
  loading: boolean;
  total: number;
}

const ProductGrid: React.FC<ProductGridProps> = ({ products, loading, total }) => {
  if (loading) {
    return (
      <div className="flex justify-center items-center py-20" data-testid="product-grid-loading">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!loading && products.length === 0) {
    return (
      <EmptyState
        icon={<Search className="h-16 w-16" />}
        title="No sarees found"
        message="Try adjusting your filters or search terms."
        ctaLabel="Clear Filters"
        ctaHref="/sarees"
      />
    );
  }

  return (
    <div data-testid="product-grid">
      <p className="text-sm text-gray-500 mb-4">{total} sarees found</p>
      <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-4">
        {products.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
    </div>
  );
};

export default ProductGrid;
