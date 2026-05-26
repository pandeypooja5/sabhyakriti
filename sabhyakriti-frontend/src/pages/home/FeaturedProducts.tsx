import { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { Product } from '@/types';
import { listProducts } from '@/services/productService';
import ProductCard from '@/components/product/ProductCard';
import LoadingSpinner from '@/components/shared/LoadingSpinner';

const FeaturedProducts: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listProducts({ sort: 'rating', pageSize: 8, page: 1 })
      .then((res) => setProducts(res.data))
      .catch(() => setProducts([]))
      .finally(() => setLoading(false));
  }, []);

  const scroll = (dir: 'left' | 'right') => {
    if (!scrollRef.current) return;
    scrollRef.current.scrollBy({ left: dir === 'right' ? 280 : -280, behavior: 'smooth' });
  };

  return (
    <section className="py-12 bg-white" data-testid="featured-products">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Featured Sarees</h2>
            <p className="text-sm text-gray-500 mt-1">Top-rated picks from our collection</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => scroll('left')}
              data-testid="featured-scroll-left"
              className="h-8 w-8 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50 transition-colors"
              aria-label="Scroll left"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              onClick={() => scroll('right')}
              data-testid="featured-scroll-right"
              className="h-8 w-8 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-50 transition-colors"
              aria-label="Scroll right"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-12"><LoadingSpinner /></div>
        ) : (
          <div
            ref={scrollRef}
            className="flex gap-4 overflow-x-auto pb-2 scroll-smooth snap-x snap-mandatory"
            style={{ scrollbarWidth: 'none' }}
          >
            {products.map((product) => (
              <div key={product.id} className="flex-shrink-0 w-56 snap-start">
                <ProductCard product={product} />
              </div>
            ))}
          </div>
        )}

        <div className="text-center mt-6">
          <Link
            to="/sarees?sort=rating"
            data-testid="featured-view-all"
            className="inline-flex items-center gap-2 text-sm font-medium text-saffron-500 hover:text-saffron-600"
          >
            View All Featured <ChevronRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </section>
  );
};

export default FeaturedProducts;
