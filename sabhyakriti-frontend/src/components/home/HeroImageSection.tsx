import { Link } from 'react-router-dom';
import { ArrowRight, Sparkles, Truck, RotateCcw } from 'lucide-react';

const HeroImageSection: React.FC = () => {
  return (
    <div className="w-full relative overflow-hidden bg-ivory-100">
      {/* Hero Image */}
      <img
        src="/hero-sarees.png"
        alt="Heritage Collection - Women in Beautiful Sarees"
        className="w-full h-auto object-cover object-center block max-w-full"
      />

      {/* Overlay for button visibility */}
      <div className="absolute inset-0 bg-black/15" />

      {/* Action Buttons + Trust Badges - Positioned on the image */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/40 to-transparent pt-16 pb-8 px-4">
        <div className="max-w-4xl mx-auto">
          {/* Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center mb-6">
            <Link
              to="/sarees"
              className="inline-flex items-center justify-center gap-2 bg-saffron-500 hover:bg-saffron-600 text-white font-semibold px-6 sm:px-8 py-3 rounded transition-colors duration-200 shadow-lg hover:shadow-xl"
            >
              Explore Collection <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              to="/sarees?sort=newest"
              className="inline-flex items-center justify-center gap-2 border-2 border-gold-300 text-white hover:bg-white/10 font-semibold px-6 sm:px-8 py-3 rounded transition-colors duration-200"
            >
              New Arrivals
            </Link>
          </div>

          {/* Trust Badges */}
          <div className="flex justify-center gap-4 text-white text-xs sm:text-sm">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-gold-300" />
              <span>5000+ Unique Designs</span>
            </div>
            <div className="flex items-center gap-2">
              <Truck className="h-4 w-4 text-gold-300" />
              <span>Free Shipping on Orders ₹999+</span>
            </div>
            <div className="flex items-center gap-2">
              <RotateCcw className="h-4 w-4 text-gold-300" />
              <span>Easy 30-Day Returns</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HeroImageSection;
