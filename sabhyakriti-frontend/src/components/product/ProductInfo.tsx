import { Share2, Copy, MessageCircle } from 'lucide-react';
import type { Product } from '@/types';
import PriceDisplay from '@/components/shared/PriceDisplay';
import StockBadge from '@/components/shared/StockBadge';
import StarRating from '@/components/shared/StarRating';
import toast from 'react-hot-toast';

interface ProductInfoProps {
  product: Product;
}

const ProductInfo: React.FC<ProductInfoProps> = ({ product }) => {
  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({ title: product.name, url: window.location.href });
      } catch { /* user cancelled */ }
    } else {
      await navigator.clipboard.writeText(window.location.href);
      toast.success('Link copied to clipboard!');
    }
  };

  const handleWhatsApp = () => {
    const text = encodeURIComponent(`Check out this beautiful saree: ${product.name}\n${window.location.href}`);
    window.open(`https://wa.me/?text=${text}`, '_blank');
  };

  return (
    <div data-testid="product-info">
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900 leading-tight" data-testid="product-name">
            {product.name}
          </h1>
          <p className="text-xs text-gray-400 mt-1">SKU: {product.sku}</p>
        </div>
        <div className="flex gap-2 flex-shrink-0">
          <button
            onClick={handleWhatsApp}
            data-testid="share-whatsapp"
            className="h-8 w-8 flex items-center justify-center rounded-full border border-gray-200 text-green-600 hover:bg-green-50 transition-colors"
            aria-label="Share on WhatsApp"
          >
            <MessageCircle className="h-4 w-4" />
          </button>
          <button
            onClick={handleShare}
            data-testid="share-btn"
            className="h-8 w-8 flex items-center justify-center rounded-full border border-gray-200 text-gray-500 hover:bg-gray-50 transition-colors"
            aria-label="Share"
          >
            {navigator.clipboard ? <Copy className="h-4 w-4" /> : <Share2 className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {/* Rating */}
      {product.reviewCount > 0 && (
        <div className="flex items-center gap-2 mb-3">
          <StarRating rating={product.avgRating} />
          <span className="text-sm text-gray-600">
            {product.avgRating.toFixed(1)} ({product.reviewCount} reviews)
          </span>
        </div>
      )}

      {/* Price */}
      <PriceDisplay price={product.price} mrp={product.mrp} size="lg" className="mb-3" />

      {/* Stock */}
      <StockBadge status={product.stockStatus} />

      {/* Description */}
      <p className="text-sm text-gray-600 mt-4 leading-relaxed" data-testid="product-description">
        {product.description}
      </p>

      {/* Categories */}
      <div className="flex flex-wrap gap-1.5 mt-4">
        {[...product.fabricCategories, ...product.occasionCategories, ...product.regionCategories].map((cat) => (
          <span key={cat.id} className="text-xs bg-teal-50 text-teal-700 px-2.5 py-1 rounded-full">
            {cat.name}
          </span>
        ))}
      </div>
    </div>
  );
};

export default ProductInfo;
