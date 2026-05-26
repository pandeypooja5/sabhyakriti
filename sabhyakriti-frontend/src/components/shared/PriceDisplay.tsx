import { formatINR, calcDiscountPercent } from '@/utils/currency';
import { cn } from '@/lib/utils';

interface PriceDisplayProps {
  price: number;
  mrp: number;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const fontSizes = {
  sm: { price: 'text-base', mrp: 'text-xs', badge: 'text-xs px-1.5 py-0.5' },
  md: { price: 'text-xl', mrp: 'text-sm', badge: 'text-xs px-2 py-0.5' },
  lg: { price: 'text-2xl', mrp: 'text-base', badge: 'text-sm px-2 py-1' },
};

const PriceDisplay: React.FC<PriceDisplayProps> = ({ price, mrp, size = 'md', className }) => {
  const discount = calcDiscountPercent(mrp, price);
  const fs = fontSizes[size];

  return (
    <div className={cn('flex items-baseline gap-2 flex-wrap', className)} data-testid="price-display">
      <span className={cn('font-bold text-gray-900', fs.price)} data-testid="price">
        {formatINR(price)}
      </span>
      {discount > 0 && (
        <>
          <span className={cn('line-through text-gray-400', fs.mrp)} data-testid="mrp">
            {formatINR(mrp)}
          </span>
          <span
            className={cn('bg-green-100 text-green-700 rounded font-semibold', fs.badge)}
            data-testid="discount-badge"
          >
            {discount}% off
          </span>
        </>
      )}
    </div>
  );
};

export default PriceDisplay;
