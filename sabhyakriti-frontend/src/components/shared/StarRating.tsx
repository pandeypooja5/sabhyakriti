import { Star } from 'lucide-react';
import { cn } from '@/lib/utils';

interface StarRatingProps {
  rating: number;
  max?: number;
  interactive?: boolean;
  onRate?: (rating: number) => void;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizes = { sm: 'h-3.5 w-3.5', md: 'h-5 w-5', lg: 'h-6 w-6' };

const StarRating: React.FC<StarRatingProps> = ({
  rating,
  max = 5,
  interactive = false,
  onRate,
  size = 'md',
  className,
}) => {
  const stars = Array.from({ length: max }, (_, i) => i + 1);

  return (
    <div className={cn('flex items-center gap-0.5', className)} role="group" aria-label={`${rating} out of ${max} stars`}>
      {stars.map((star) => {
        const filled = star <= Math.round(rating);
        const partial = !filled && star - 1 < rating && rating < star;

        return (
          <button
            key={star}
            type="button"
            disabled={!interactive}
            data-testid={`star-${star}`}
            onClick={() => interactive && onRate?.(star)}
            className={cn(
              'focus:outline-none transition-transform',
              interactive && 'hover:scale-110 cursor-pointer',
              !interactive && 'cursor-default pointer-events-none'
            )}
            aria-label={`Rate ${star} stars`}
          >
            <Star
              className={cn(
                sizes[size],
                filled ? 'fill-gold-600 text-gold-600' : '',
                partial ? 'fill-gold-200 text-gold-600' : '',
                !filled && !partial ? 'fill-ivory-300 text-ivory-300' : ''
              )}
            />
          </button>
        );
      })}
    </div>
  );
};

export default StarRating;
