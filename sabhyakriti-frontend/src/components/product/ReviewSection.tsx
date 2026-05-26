import { useState, useEffect } from 'react';
import type { Review } from '@/types';
import { listReviews, submitReview } from '@/services/reviewService';
import ReviewCard from './ReviewCard';
import StarRating from '@/components/shared/StarRating';
import { useAuth } from '@/hooks/useAuth';
import LoadingSpinner from '@/components/shared/LoadingSpinner';
import toast from 'react-hot-toast';

interface ReviewSectionProps {
  productId: string;
  avgRating: number;
  reviewCount: number;
}

const ReviewSection: React.FC<ReviewSectionProps> = ({ productId, avgRating, reviewCount }) => {
  const { isAuthenticated } = useAuth();
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Review form state
  const [rating, setRating] = useState(0);
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [formOpen, setFormOpen] = useState(false);

  useEffect(() => {
    setLoading(true);
    listReviews(productId, page, 5)
      .then((res) => {
        setReviews(res.data);
        setTotalPages(res.totalPages);
      })
      .catch(() => null)
      .finally(() => setLoading(false));
  }, [productId, page]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rating === 0) { toast.error('Please select a rating'); return; }
    setSubmitting(true);
    try {
      const newReview = await submitReview({ productId, rating, title, body });
      setReviews((prev) => [newReview, ...prev]);
      toast.success('Review submitted!');
      setFormOpen(false);
      setRating(0); setTitle(''); setBody('');
    } catch {
      toast.error('Failed to submit review');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="mt-10" data-testid="review-section">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">Customer Reviews</h2>
        {isAuthenticated && !formOpen && (
          <button
            onClick={() => setFormOpen(true)}
            data-testid="write-review-btn"
            className="text-sm font-medium text-saffron-500 hover:text-saffron-600 border border-saffron-500 px-3 py-1.5 rounded-lg"
          >
            Write a Review
          </button>
        )}
      </div>

      {/* Summary */}
      <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-xl mb-4">
        <div className="text-center">
          <p className="text-4xl font-bold text-gray-900">{avgRating.toFixed(1)}</p>
          <StarRating rating={avgRating} size="sm" className="mt-1" />
          <p className="text-xs text-gray-500 mt-1">{reviewCount} reviews</p>
        </div>
      </div>

      {/* Review Form */}
      {formOpen && (
        <form onSubmit={handleSubmit} className="bg-gray-50 rounded-xl p-4 mb-4" data-testid="review-form">
          <h3 className="font-semibold text-gray-800 mb-3">Your Review</h3>
          <div className="mb-3">
            <label className="text-sm text-gray-700 mb-1 block">Rating *</label>
            <StarRating rating={rating} interactive onRate={setRating} size="lg" />
          </div>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Review title"
            data-testid="review-title-input"
            required
            className="input-field mb-2"
          />
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Share your experience..."
            data-testid="review-body-input"
            required
            rows={3}
            className="input-field mb-3 resize-none"
          />
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={submitting}
              data-testid="review-submit-btn"
              className="btn-primary text-sm py-2 px-4"
            >
              {submitting ? 'Submitting...' : 'Submit Review'}
            </button>
            <button
              type="button"
              onClick={() => setFormOpen(false)}
              className="text-sm text-gray-500 hover:text-gray-700 px-4"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Review List */}
      {loading ? (
        <div className="py-8 flex justify-center"><LoadingSpinner /></div>
      ) : reviews.length === 0 ? (
        <p className="text-sm text-gray-500 py-6 text-center">No reviews yet. Be the first to review!</p>
      ) : (
        <>
          <div>
            {reviews.map((review) => (
              <ReviewCard key={review.id} review={review} />
            ))}
          </div>
          {totalPages > 1 && (
            <div className="flex gap-2 mt-4 justify-center">
              {page > 1 && (
                <button
                  onClick={() => setPage((p) => p - 1)}
                  data-testid="reviews-prev"
                  className="text-sm text-saffron-500 hover:text-saffron-600 font-medium"
                >
                  Prev
                </button>
              )}
              <span className="text-sm text-gray-500">Page {page} of {totalPages}</span>
              {page < totalPages && (
                <button
                  onClick={() => setPage((p) => p + 1)}
                  data-testid="reviews-next"
                  className="text-sm text-saffron-500 hover:text-saffron-600 font-medium"
                >
                  Next
                </button>
              )}
            </div>
          )}
        </>
      )}
    </section>
  );
};

export default ReviewSection;
