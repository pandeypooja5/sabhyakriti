import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

interface Category {
  title: string;
  description: string;
  href: string;
}

const categories: Category[] = [
  {
    title: 'By Craft',
    description: 'Banarasi, Kanjivaram, Jamdani & traditional weaves',
    href: '/sarees?filterBy=fabric',
  },
  {
    title: 'By Occasion',
    description: 'Wedding, Festive, Party, Casual & professional sarees',
    href: '/sarees?filterBy=occasion',
  },
  {
    title: 'By Heritage Region',
    description: 'Bengal, Varanasi, Kanchipuram, Rajasthan & more',
    href: '/sarees?filterBy=region',
  },
];

const WorldOfSabhyaKritiSection: React.FC = () => {
  return (
    <div
      className="w-full py-20 px-4 sm:px-6 lg:px-8 relative"
      style={{
        background: 'linear-gradient(135deg, #FAF4EA 0%, #F5EBD8 50%, #FAF4EA 100%)',
      }}
    >
      {/* Subtle floral motif background pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute top-10 right-20 text-6xl">❁</div>
        <div className="absolute bottom-10 left-20 text-6xl">❁</div>
        <div className="absolute top-1/2 right-10 text-5xl">✿</div>
        <div className="absolute top-1/3 left-1/4 text-5xl">✿</div>
      </div>

      <div className="max-w-5xl mx-auto relative z-10">
        {/* Heading */}
        <div className="text-center mb-16">
          <h2 className="font-playfair text-4xl sm:text-5xl font-normal text-brand-text">
            The World of SabhyaKriti
          </h2>
        </div>

        {/* Category Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
          {categories.map((category) => (
            <div
              key={category.title}
              className="bg-white/60 backdrop-blur-sm p-8 rounded-lg transition-all duration-300 hover:bg-white/80 hover:shadow-sm"
            >
              {/* Category Title */}
              <h3 className="font-playfair text-2xl font-normal text-brand-text mb-3">
                {category.title}
              </h3>

              {/* Category Description */}
              <p className="font-cormorant text-sm text-brand-textMuted leading-relaxed mb-6 italic">
                {category.description}
              </p>

              {/* Explore Link */}
              <Link
                to={category.href}
                className="inline-flex items-center gap-2 text-gold-700 hover:text-gold-800 font-medium text-sm transition-colors duration-200"
              >
                Explore <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          ))}
        </div>

        {/* Bottom Tagline */}
        <div className="text-center mt-16">
          <p className="font-cormorant text-lg text-brand-text italic">
            Timeless Elegance, Crafted for You
          </p>
        </div>
      </div>
    </div>
  );
};

export default WorldOfSabhyaKritiSection;
