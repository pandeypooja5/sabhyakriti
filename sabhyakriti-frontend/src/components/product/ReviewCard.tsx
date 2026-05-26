import { BadgeCheck } from 'lucide-react';
import type { Review } from '@/types';
import StarRating from '@/components/shared/StarRating';
import { timeAgo } from '@/utils/date';

interface ReviewCardProps {
  review: Review;
}

const ReviewCard: React.FC<ReviewCardProps> = ({ review }) => {
  return (
    <div className="py-4 border-b border-gray-100 last:border-0" data-testid="review-card">
      <div className="flex items-start gap-3">
        <div className="h-9 w-9 rounded-full bg-teal-100 flex items-center justify-center text-teal-700 font-bold text-sm flex-shrink-0">
          {review.user.name[0]?.toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-sm text-gray-900">{review.user.name}</span>
            {review.isVerifiedPurchase && (
              <span className="flex items-center gap-1 text-xs text-green-600 font-medium">
                <BadgeCheck className="h-3.5 w-3.5" /> Verified Purchase
              </span>
            )}
            <span className="text-xs text-gray-400 ml-auto">{timeAgo(review.createdAt)}</span>
          </div>
          <StarRating rating={review.rating} size="sm" className="mt-1 mb-1.5" />
          <h4 className="text-sm font-semibold text-gray-800 mb-1">{review.title}</h4>
          <p className="text-sm text-gray-600 leading-relaxed">{review.body}</p>
        </div>
      </div>
    </div>
  );
};

export default ReviewCard;
