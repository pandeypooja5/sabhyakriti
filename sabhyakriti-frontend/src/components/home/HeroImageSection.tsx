import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

const HeroImageSection: React.FC = () => {
  return (
    <div className="w-full relative overflow-hidden">
      {/* Hero Image */}
      <img
        src="/hero-sarees.png"
        alt="SabhyaKriti - Elegance of Indian Tradition"
        className="w-full h-auto object-cover object-center block max-w-full"
      />

      {/* Right-side text overlay — mirrors the Copilot image style */}
      <div className="absolute inset-0 flex items-center justify-end pr-8 sm:pr-16 lg:pr-24">
        <div className="text-right max-w-xs sm:max-w-sm">
          {/* Brand name */}
          <h1 className="font-playfair text-4xl sm:text-5xl font-bold mb-2 leading-tight drop-shadow-lg">
            <span style={{ color: '#C9A042' }}>Sabhya</span>
            <span style={{ color: '#8B1A1A' }}>Kriti</span>
          </h1>

          {/* Tagline */}
          <p className="font-cormorant italic text-lg sm:text-xl text-white drop-shadow mb-1">
            Elegance of Indian Tradition
          </p>

          {/* Sub-taglines */}
          <p className="text-white/90 text-sm sm:text-base mb-6 drop-shadow">
            Exquisite Ethnic Wear · Timeless Craftsmanship
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 justify-end">
            <Link
              to="/sarees?category=women"
              className="inline-flex items-center justify-center gap-2 bg-saffron-500 hover:bg-saffron-600 text-white font-semibold px-6 py-2.5 rounded transition-colors duration-200 shadow-lg text-sm"
            >
              Shop Women <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              to="/sarees?category=men"
              className="inline-flex items-center justify-center gap-2 border-2 border-white/80 text-white hover:bg-white/10 font-semibold px-6 py-2.5 rounded transition-colors duration-200 text-sm"
            >
              Shop Men
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HeroImageSection;
