import { useEffect, useCallback } from 'react';
import { X, ChevronLeft, ChevronRight } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '@/store/store';
import { closeLightbox, setLightboxIndex } from '@/store/slices/uiSlice';

const ImageLightbox: React.FC = () => {
  const dispatch = useAppDispatch();
  const { open, images, currentIndex } = useAppSelector((s) => s.ui.modals.lightbox);

  const prev = useCallback(() => {
    dispatch(setLightboxIndex((currentIndex - 1 + images.length) % images.length));
  }, [dispatch, currentIndex, images.length]);

  const next = useCallback(() => {
    dispatch(setLightboxIndex((currentIndex + 1) % images.length));
  }, [dispatch, currentIndex, images.length]);

  // Keyboard navigation
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') dispatch(closeLightbox());
      if (e.key === 'ArrowLeft') prev();
      if (e.key === 'ArrowRight') next();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [open, dispatch, prev, next]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center"
      data-testid="image-lightbox"
      role="dialog"
      aria-modal="true"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/90"
        onClick={() => dispatch(closeLightbox())}
      />

      {/* Close button */}
      <button
        onClick={() => dispatch(closeLightbox())}
        data-testid="lightbox-close"
        className="absolute top-4 right-4 z-10 h-10 w-10 flex items-center justify-center rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
        aria-label="Close lightbox"
      >
        <X className="h-5 w-5" />
      </button>

      {/* Prev */}
      {images.length > 1 && (
        <button
          onClick={prev}
          data-testid="lightbox-prev"
          className="absolute left-4 z-10 h-10 w-10 flex items-center justify-center rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
          aria-label="Previous image"
        >
          <ChevronLeft className="h-5 w-5" />
        </button>
      )}

      {/* Image */}
      <div className="relative z-10 max-h-[90vh] max-w-[90vw]">
        <img
          src={images[currentIndex]}
          alt={`Image ${currentIndex + 1}`}
          className="max-h-[90vh] max-w-[90vw] object-contain rounded-lg"
          data-testid="lightbox-image"
        />
        <p className="text-center text-white/60 text-sm mt-2">
          {currentIndex + 1} / {images.length}
        </p>
      </div>

      {/* Next */}
      {images.length > 1 && (
        <button
          onClick={next}
          data-testid="lightbox-next"
          className="absolute right-4 z-10 h-10 w-10 flex items-center justify-center rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
          aria-label="Next image"
        >
          <ChevronRight className="h-5 w-5" />
        </button>
      )}
    </div>
  );
};

export default ImageLightbox;
