import { Zap, ChevronLeft, ChevronRight } from 'lucide-react';
import { useState, useEffect } from 'react';

interface FeaturedProduct {
  id: number;
  name: string;
  image: string;
  discount: string;
}

const FlashSaleBanner: React.FC = () => {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [timeLeft, setTimeLeft] = useState<string>('');

  // Featured products with placeholder images
  const featuredProducts: FeaturedProduct[] = [
    { id: 1, name: 'Banarasi Silk', image: '🥻', discount: '-20%' },
    { id: 2, name: 'Kanjivaram Silk', image: '🥻', discount: '-25%' },
    { id: 3, name: 'Jamdani Muslin', image: '🥻', discount: '-15%' },
    { id: 4, name: 'Chanderi Silk', image: '🥻', discount: '-30%' },
    { id: 5, name: 'Patola Silk', image: '🥻', discount: '-18%' },
    { id: 6, name: 'Bengal Tant', image: '🥻', discount: '-22%' },
  ];

  // Auto-rotate slides
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % featuredProducts.length);
    }, 4000);
    return () => clearInterval(timer);
  }, []);

  // Countdown timer
  useEffect(() => {
    const updateTimer = () => {
      const now = new Date();
      const tomorrow = new Date(now);
      tomorrow.setDate(tomorrow.getDate() + 1);
      tomorrow.setHours(0, 0, 0, 0);

      const diff = tomorrow.getTime() - now.getTime();
      const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
      const minutes = Math.floor((diff / 1000 / 60) % 60);
      const seconds = Math.floor((diff / 1000) % 60);

      setTimeLeft(`${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`);
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, []);

  const goToPrevious = () => {
    setCurrentSlide((prev) => (prev - 1 + featuredProducts.length) % featuredProducts.length);
  };

  const goToNext = () => {
    setCurrentSlide((prev) => (prev + 1) % featuredProducts.length);
  };

  return (
    <div className="w-full bg-gradient-to-br from-ivory-100 via-ivory-50 to-ivory-100 border-2 border-gold-500/30 rounded-lg overflow-hidden mb-8 shadow-sm">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-0">
        {/* Left: Carousel */}
        <div className="bg-ivory-200 relative h-96 md:h-auto flex items-center justify-center overflow-hidden">
          {/* Carousel Container */}
          <div className="relative w-full h-full flex items-center justify-center">
            {/* Product Image */}
            <div className="text-center">
              <div className="text-8xl mb-4 animate-pulse">
                {featuredProducts[currentSlide].image}
              </div>
              <div className="absolute top-4 right-4 bg-burgundy-500 text-white px-3 py-1 rounded-full text-sm font-bold">
                {featuredProducts[currentSlide].discount}
              </div>
            </div>

            {/* Navigation Arrows */}
            <button
              onClick={goToPrevious}
              className="absolute left-4 top-1/2 -translate-y-1/2 bg-gold-600 hover:bg-gold-700 text-white p-2 rounded-full transition-colors z-10"
              aria-label="Previous slide"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <button
              onClick={goToNext}
              className="absolute right-4 top-1/2 -translate-y-1/2 bg-gold-600 hover:bg-gold-700 text-white p-2 rounded-full transition-colors z-10"
              aria-label="Next slide"
            >
              <ChevronRight className="h-5 w-5" />
            </button>

            {/* Slide Indicators */}
            <div className="absolute bottom-4 flex gap-2">
              {featuredProducts.map((_, idx) => (
                <button
                  key={idx}
                  onClick={() => setCurrentSlide(idx)}
                  className={`h-2 rounded-full transition-all ${
                    idx === currentSlide
                      ? 'bg-gold-600 w-8'
                      : 'bg-gold-300 w-2 hover:bg-gold-400'
                  }`}
                  aria-label={`Go to slide ${idx + 1}`}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Right: Content */}
        <div className="p-8 md:p-12 flex flex-col justify-center bg-white">
          {/* Eyebrow */}
          <div className="flex items-center gap-2 mb-4">
            <Zap className="h-5 w-5 text-burgundy-500" />
            <span className="font-cormorant text-xs italic tracking-widest uppercase text-burgundy-500">
              Limited Time Offer
            </span>
          </div>

          {/* Heading */}
          <h2 className="font-playfair text-4xl md:text-5xl font-normal text-brand-text mb-3 leading-tight">
            Flash Sale Now On!
          </h2>

          {/* Tagline */}
          <p className="font-cormorant text-lg italic text-[#7A6050] mb-6">
            Score Big Savings on All Your Favorites.
          </p>

          {/* Main Message */}
          <div className="mb-8 p-6 bg-gold-50 border-l-4 border-gold-600 rounded">
            <p className="font-cormorant text-2xl text-brand-text mb-2">
              <span className="font-playfair font-bold">Up to 40% OFF</span>
            </p>
            <p className="text-sm text-brand-textMuted">
              On selected heritage collection sarees
            </p>
          </div>

          {/* Timer */}
          <div className="mb-8 flex items-center gap-4">
            <div className="text-center flex-1">
              <p className="text-xs font-cormorant italic text-brand-textMuted mb-2 uppercase tracking-wide">
                Offer Ends In
              </p>
              <div className="font-mono text-3xl font-bold text-burgundy-600 tracking-wider">
                {timeLeft || '00:00:00'}
              </div>
            </div>
          </div>

          {/* CTA Button */}
          <button className="w-full bg-burgundy-500 hover:bg-burgundy-600 text-white font-semibold py-4 rounded transition-colors duration-200 flex items-center justify-center gap-2 text-lg">
            <span>Explore Now</span>
            <span className="text-2xl">🛍️</span>
          </button>

          {/* Promo Code */}
          <div className="mt-6 pt-6 border-t border-ivory-300 text-center">
            <p className="text-xs text-brand-textMuted mb-2 font-cormorant italic">Use Code</p>
            <p className="font-mono text-lg font-bold text-gold-700 bg-ivory-100 py-2 px-4 rounded inline-block">
              FLASH40
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FlashSaleBanner;
