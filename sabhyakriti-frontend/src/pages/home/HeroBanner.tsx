import { Link } from 'react-router-dom';
import { ArrowRight, Sparkles } from 'lucide-react';

const HeroBanner: React.FC = () => {
  return (
    <section
      data-testid="hero-banner"
      className="relative overflow-hidden bg-gradient-to-br from-teal-800 via-teal-700 to-teal-900 text-white"
    >
      {/* Decorative circles */}
      <div className="absolute -top-16 -right-16 h-64 w-64 rounded-full bg-saffron-500 opacity-10" />
      <div className="absolute -bottom-8 -left-8 h-48 w-48 rounded-full bg-saffron-400 opacity-10" />
      <div className="absolute top-1/2 right-1/3 h-32 w-32 rounded-full bg-teal-500 opacity-20" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-24 lg:py-32">
        <div className="max-w-2xl">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="h-4 w-4 text-saffron-400" />
            <span className="text-sm font-medium text-saffron-300 uppercase tracking-wider">
              New Season Collection
            </span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight mb-6">
            Discover{' '}
            <span className="text-saffron-400">Timeless</span>
            <br />
            Elegance
          </h1>

          <p className="text-lg sm:text-xl text-teal-100 mb-8 leading-relaxed">
            Handpicked sarees from master weavers across India.
            Each drape tells a story of heritage, craft, and beauty.
          </p>

          <div className="flex flex-col sm:flex-row gap-3">
            <Link
              to="/sarees"
              data-testid="hero-shop-now"
              className="inline-flex items-center justify-center gap-2 bg-saffron-500 hover:bg-saffron-600 text-white font-semibold px-8 py-3.5 rounded-xl transition-colors duration-200 shadow-lg hover:shadow-xl"
            >
              Shop Now <ArrowRight className="h-5 w-5" />
            </Link>
            <Link
              to="/sarees?sort=newest"
              data-testid="hero-new-arrivals"
              className="inline-flex items-center justify-center gap-2 border-2 border-white/30 hover:border-white/60 text-white font-semibold px-8 py-3.5 rounded-xl transition-colors duration-200 backdrop-blur-sm"
            >
              New Arrivals
            </Link>
          </div>

          {/* Trust badges */}
          <div className="flex flex-wrap gap-4 mt-10">
            {[
              '500+ Unique Designs',
              'Free Shipping ₹999+',
              'Easy 30-Day Returns',
              'Handcrafted by Artisans',
            ].map((badge) => (
              <span
                key={badge}
                className="text-xs text-teal-200 flex items-center gap-1"
              >
                <span className="h-1.5 w-1.5 rounded-full bg-saffron-400 flex-shrink-0" />
                {badge}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom wave */}
      <div className="absolute bottom-0 left-0 right-0 h-8 bg-[#FAFAFA]" style={{ clipPath: 'ellipse(60% 100% at 50% 100%)' }} />
    </section>
  );
};

export default HeroBanner;
