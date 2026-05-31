import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

const HeroImageSection: React.FC = () => {
  return (
    <div className="w-full relative overflow-hidden">
      {/* Hero Image */}
      <img
        src="/hero-sarees.png"
        alt="SabhyaKriti - Saree Collection"
        className="w-full h-auto object-cover object-center block max-w-full"
      />

      {/* Cover the image's baked-in "Shop Now" button (bottom-center ~75% down) */}
      <div
        className="absolute left-1/2 -translate-x-1/2"
        style={{ bottom: '14%', width: '160px', height: '48px', background: 'rgba(255,255,255,0.0)' }}
      >
        {/* White block to paint over the image button */}
        <div className="absolute inset-0 bg-white/90 rounded" />
      </div>

      {/* Our Shop Now button — positioned over the covered area */}
      <div
        className="absolute left-1/2 -translate-x-1/2"
        style={{ bottom: '14%' }}
      >
        <Link
          to="/sarees"
          className="inline-flex items-center gap-2 bg-saffron-500 hover:bg-saffron-600 text-white font-semibold px-10 py-3 rounded transition-colors duration-200 shadow-lg text-sm sm:text-base whitespace-nowrap"
        >
          Shop Now <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
};

export default HeroImageSection;
