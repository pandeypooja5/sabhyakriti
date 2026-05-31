import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

const HeroImageSection: React.FC = () => {
  return (
    <div className="w-full relative overflow-hidden">
      {/* Hero Image — text already baked into the image */}
      <img
        src="/hero-sarees.png"
        alt="SabhyaKriti - Elegance of Indian Tradition"
        className="w-full h-auto object-cover object-center block max-w-full"
      />

      {/* Single CTA button */}
      <div className="absolute bottom-6 sm:bottom-10 left-0 right-0 flex justify-center px-4">
        <Link
          to="/sarees"
          className="inline-flex items-center gap-2 bg-saffron-500 hover:bg-saffron-600 text-white font-semibold px-10 py-3 rounded transition-colors duration-200 shadow-lg text-sm sm:text-base"
        >
          Shop Now <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
};

export default HeroImageSection;
