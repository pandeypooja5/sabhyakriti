import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import type { Product } from '@/types';
import { listProducts } from '@/services/productService';
import ProductCard from '@/components/product/ProductCard';
import LoadingSpinner from '@/components/shared/LoadingSpinner';

const NewArrivals: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listProducts({ sort: 'newest', pageSize: 8, page: 1 })
      .then((res) => setProducts(res.data))
      .catch(() => setProducts([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className="py-16 bg-ivory-100" data-testid="new-arrivals">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <p className="font-cormorant text-sm text-gold-600 italic tracking-widest uppercase mb-2">
              Fresh from the Loom
            </p>
            <h2 className="font-playfair text-4xl sm:text-5xl font-normal text-brand-text">New Arrivals</h2>
          </div>
          <Link
            to="/sarees?sort=newest"
            data-testid="new-arrivals-view-all"
            className="text-sm font-medium text-gold-700 hover:text-gold-800 flex items-center gap-1"
          >
            View All <ChevronRight className="h-4 w-4" />
          </Link>
        </div>

        {loading ? (
          <div className="flex justify-center py-12"><LoadingSpinner /></div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
};

export default NewArrivals;
