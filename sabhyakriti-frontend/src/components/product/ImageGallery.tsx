import { useState } from 'react';
import Zoom from 'react-medium-image-zoom';
import 'react-medium-image-zoom/dist/styles.css';
import type { ProductImage } from '@/types';
import { cn } from '@/lib/utils';

interface ImageGalleryProps {
  images: ProductImage[];
  productName: string;
}

const ImageGallery: React.FC<ImageGalleryProps> = ({ images, productName }) => {
  const sorted = [...images].sort((a, b) => a.sortOrder - b.sortOrder);
  const [selectedIdx, setSelectedIdx] = useState(
    sorted.findIndex((i) => i.isPrimary) >= 0 ? sorted.findIndex((i) => i.isPrimary) : 0
  );

  const current = sorted[selectedIdx];

  return (
    <div className="flex gap-3" data-testid="image-gallery">
      {/* Thumbnails */}
      {sorted.length > 1 && (
        <div className="flex flex-col gap-2 w-16 flex-shrink-0">
          {sorted.map((img, idx) => (
            <button
              key={img.id}
              onClick={() => setSelectedIdx(idx)}
              data-testid={`thumbnail-${idx}`}
              className={cn(
                'h-16 w-16 rounded-lg overflow-hidden border-2 transition-colors flex-shrink-0',
                idx === selectedIdx ? 'border-saffron-500' : 'border-transparent hover:border-gray-300'
              )}
              aria-label={`View image ${idx + 1}`}
            >
              <img
                src={img.url}
                alt={img.altText ?? `${productName} view ${idx + 1}`}
                className="h-full w-full object-cover"
              />
            </button>
          ))}
        </div>
      )}

      {/* Main Image with zoom */}
      <div className="flex-1 rounded-2xl overflow-hidden bg-gray-100 aspect-square" data-testid="main-image-container">
        <Zoom>
          <img
            src={current?.url ?? '/placeholder.jpg'}
            alt={current?.altText ?? productName}
            className="h-full w-full object-cover cursor-zoom-in"
            data-testid="main-product-image"
          />
        </Zoom>
      </div>
    </div>
  );
};

export default ImageGallery;
