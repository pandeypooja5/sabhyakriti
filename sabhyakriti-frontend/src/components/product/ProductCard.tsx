import { Link } from 'react-router-dom';
import { Heart } from 'lucide-react';
import type { Product } from '@/types';
import { formatINR, calcDiscountPercent } from '@/utils/currency';
import StarRating from '@/components/shared/StarRating';
import StockBadge from '@/components/shared/StockBadge';
import { useWishlist } from '@/hooks/useWishlist';
import { useAuth } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';
import toast from 'react-hot-toast';

interface ProductCardProps {
  product: Product;
  className?: string;
}

const ProductCard: React.FC<ProductCardProps> = ({ product, className }) => {
  const { isWishlisted, toggle } = useWishlist();
  const { isAuthenticated } = useAuth();
  const wishlisted = isWishlisted(product.id);
  const discount = calcDiscountPercent(product.mrp, product.price);
  const primaryImage = product.images.find((i) => i.isPrimary) ?? product.images[0];

  const handleWishlistToggle = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isAuthenticated) {
      toast.error('Please login to save to wishlist');
      return;
    }
    await toggle(product.id);
    toast.success(wishlisted ? 'Removed from wishlist' : 'Added to wishlist');
  };

  return (
    <article
      className={cn('card group relative hover:shadow-[0_4px_20px_rgba(201,160,66,0.12)] transition-shadow duration-200', className)}
      data-testid="product-card"
    >
      {/* Image */}
      <div className="relative overflow-hidden bg-ivory-200 aspect-[3/4]">
        <Link to={`/sarees/${product.slug}`} data-testid="product-card-link">
          {primaryImage?.url ? (
            <img
              src={primaryImage.url}
              alt={product.name}
              className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-300"
              loading="lazy"
              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
            />
          ) : (
            <div className="h-full w-full flex flex-col items-center justify-center bg-gradient-to-br from-ivory-200 via-ivory-100 to-ivory-300 group-hover:scale-105 transition-transform duration-300">
              <span className="text-4xl mb-2">🥻</span>
              <span className="text-xs text-brand-textMuted font-medium text-center px-2 line-clamp-2">{product.name}</span>
            </div>
          )}
        </Link>

        {/* Discount badge */}
        {discount > 0 && (
          <span
            className="absolute top-2 left-2 bg-burgundy-500 text-white text-xs font-bold px-2 py-0.5 rounded"
            data-testid="product-card-discount"
          >
            -{discount}%
          </span>
        )}

        {/* Stock badge */}
        {product.stockStatus !== 'IN_STOCK' && (
          <div className="absolute top-2 right-2">
            <StockBadge status={product.stockStatus} />
          </div>
        )}

        {/* Wishlist button */}
        <button
          onClick={handleWishlistToggle}
          data-testid="product-card-wishlist"
          aria-label={wishlisted ? 'Remove from wishlist' : 'Add to wishlist'}
          className={cn(
            'absolute bottom-2 right-2 h-8 w-8 rounded-full flex items-center justify-center shadow transition-all duration-200',
            wishlisted
              ? 'bg-burgundy-500 text-white'
              : 'bg-ivory-100 text-brand-textMuted opacity-0 group-hover:opacity-100 hover:text-burgundy-500'
          )}
        >
          <Heart className={cn('h-4 w-4', wishlisted && 'fill-current')} />
        </button>
      </div>

      {/* Info */}
      <div className="p-4">
        <Link to={`/sarees/${product.slug}`}>
          <h3
            className="text-sm font-medium text-brand-text line-clamp-2 hover:text-gold-700 transition-colors mb-1"
            data-testid="product-card-name"
          >
            {product.name}
          </h3>
        </Link>

        {/* Artisan attribution */}
        {product.regionCategories?.[0]?.name && (
          <p className="font-cormorant text-xs text-[#7A6050] italic tracking-wide mb-1">
            {product.regionCategories[0].name} craft
          </p>
        )}

        {/* Rating */}
        {product.reviewCount > 0 && (
          <div className="flex items-center gap-1.5 mb-2">
            <StarRating rating={product.avgRating} size="sm" />
            <span className="text-xs text-brand-textMuted">({product.reviewCount})</span>
          </div>
        )}

        {/* Price */}
        <div className="flex items-baseline gap-1.5 flex-wrap">
          <span className="font-bold text-brand-text text-base" data-testid="product-card-price">
            {formatINR(product.price)}
          </span>
          {discount > 0 && (
            <span className="text-xs text-brand-textMuted line-through" data-testid="product-card-mrp">
              {formatINR(product.mrp)}
            </span>
          )}
        </div>
      </div>
    </article>
  );
};

export default ProductCard;
