import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

const HeroBanner: React.FC = () => {
  return (
    <div className="w-full h-full flex items-center justify-center px-8 py-12">
      <div className="max-w-md">
        {/* Gold eyebrow line */}
        <div className="flex items-center gap-3 mb-6">
          <div className="h-px bg-gold-600 w-8" />
          <span className="text-xs font-cormorant italic text-gold-600 tracking-widest uppercase">
            Heritage Collection
          </span>
        </div>

        {/* Main heading with emphasis */}
        <h1 className="font-playfair text-4xl sm:text-5xl font-normal text-brand-text leading-tight mb-6">
          Woven in <em className="italic text-gold-600">Tradition.</em>
          <br />
          Worn with <em className="italic text-burgundy-500">Grace.</em>
        </h1>

        {/* Subtitle */}
        <p className="font-cormorant text-lg text-brand-textMuted italic leading-relaxed mb-8">
          Discover handcrafted sarees from master weavers across India.
          Each drape tells a story of heritage, craft, and timeless beauty.
        </p>

        {/* CTA buttons */}
        <div className="flex flex-col sm:flex-row gap-4 mb-10">
          <Link
            to="/sarees"
            data-testid="hero-shop-now"
            className="inline-flex items-center justify-center gap-2 bg-saffron-500 hover:bg-saffron-600 text-white font-semibold px-8 py-3.5 rounded transition-colors duration-200 shadow-lg hover:shadow-xl"
          >
            Explore Collection <ArrowRight className="h-5 w-5" />
          </Link>
          <Link
            to="/sarees?sort=newest"
            data-testid="hero-new-arrivals"
            className="inline-flex items-center justify-center gap-2 border-2 border-gold-600 text-gold-600 hover:bg-gold-50 font-semibold px-8 py-3.5 rounded transition-colors duration-200"
          >
            New Arrivals
          </Link>
        </div>

        {/* Trust badges */}
        <div className="flex flex-wrap gap-4">
          {[
            '500+ Unique Designs',
            'Free Shipping ₹999+',
            'Easy 30-Day Returns',
            'Handcrafted by Artisans',
          ].map((badge) => (
            <span
              key={badge}
              className="text-xs text-brand-textMuted flex items-center gap-2"
            >
              <span className="h-2 w-2 rounded-full bg-gold-600 flex-shrink-0" />
              {badge}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default HeroBanner;
