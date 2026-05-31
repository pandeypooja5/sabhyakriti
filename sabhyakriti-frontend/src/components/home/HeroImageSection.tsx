import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

const HeroImageSection: React.FC = () => {
  return (
    <div className="w-full relative overflow-hidden">
      {/* Crop out the baked-in "Shop Now" button by hiding the bottom ~18% of the image */}
      <div className="w-full overflow-hidden" style={{ maxHeight: '82%' }}>
        <img
          src="/hero-sarees.png"
          alt="SabhyaKriti - Saree Collection"
          className="w-full h-auto object-cover object-top block max-w-full"
          style={{ marginBottom: '-18%' }}
        />
      </div>

      {/* Our Shop Now button — floats over the cropped edge */}
      <div className="absolute bottom-4 sm:bottom-6 left-0 right-0 flex justify-center">
        <Link
          to="/sarees"
          className="inline-flex items-center gap-2 bg-saffron-500 hover:bg-saffron-600 text-white font-semibold px-10 py-3 rounded transition-colors duration-200 shadow-xl text-sm sm:text-base"
        >
          Shop Now <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  );
};

export default HeroImageSection;
