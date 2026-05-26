import { useEffect, useState, useRef } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { Product } from '@/types';
import { getRelatedProducts } from '@/services/productService';
import ProductCard from './ProductCard';

interface RelatedProductsProps {
  productId: string;
}

const RelatedProducts: React.FC<RelatedProductsProps> = ({ productId }) => {
  const [products, setProducts] = useState<Product[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getRelatedProducts(productId)
      .then(setProducts)
      .catch(() => null);
  }, [productId]);

  if (products.length === 0) return null;

  const scroll = (dir: 'left' | 'right') => {
    scrollRef.current?.scrollBy({ left: dir === 'right' ? 240 : -240, behavior: 'smooth' });
  };

  return (
    <section className="mt-12" data-testid="related-products">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">You May Also Like</h2>
        <div className="flex gap-2">
          <button
            onClick={() => scroll('left')}
            data-testid="related-scroll-left"
            className="h-8 w-8 rounded-full border border-gray-200 flex items-center justify-center hover:bg-gray-50"
            aria-label="Scroll left"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button
            onClick={() => scroll('right')}
            data-testid="related-scroll-right"
            className="h-8 w-8 rounded-full border border-gray-200 flex items-center justify-center hover:bg-gray-50"
            aria-label="Scroll right"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
      <div
        ref={scrollRef}
        className="flex gap-4 overflow-x-auto pb-2 scroll-smooth"
        style={{ scrollbarWidth: 'none' }}
      >
        {products.map((product) => (
          <div key={product.id} className="flex-shrink-0 w-52">
            <ProductCard product={product} />
          </div>
        ))}
      </div>
    </section>
  );
};

export default RelatedProducts;
