import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

const crafts = [
  {
    name: 'Banarasi Silk',
    region: 'Varanasi',
    story:
      'The jewel of Indian textiles. For centuries, master weavers in Varanasi have crafted silk sarees using gold and silver threads, creating intricate patterns that tell stories of devotion and artistry.',
    details: 'Hand-woven • Gold Zari • Ornate Borders',
    href: '/sarees?fabric=banarasi',
  },
  {
    name: 'Kanjivaram Silk',
    region: 'Tamil Nadu',
    story:
      'A symbol of South Indian tradition. These heavyweight silk sarees with their distinctive borders and pallu represent centuries of weaving excellence, passed down through generations of artisan families.',
    details: 'Pure Silk • Rich Colors • Bold Designs',
    href: '/sarees?fabric=kanjivaram',
  },
  {
    name: 'Jamdani Muslin',
    region: 'Bengal',
    story:
      'The gossamer fabric of emperors. Jamdani technique involves adding supplementary weft threads to create intricate floral and geometric patterns. These ethereal drapes are perfect for summer elegance.',
    details: 'Hand-loomed • Breathable • Delicate Patterns',
    href: '/sarees?fabric=jamdani',
  },
];

const CraftStorySection: React.FC = () => {
  return (
    <section className="py-16 px-4 sm:px-6 lg:px-8 bg-ivory-100" data-testid="craft-story-section">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-16">
          <p className="font-cormorant text-sm text-gold-600 italic tracking-widest uppercase mb-2">
            Heritage & Craft
          </p>
          <h2 className="font-playfair text-4xl sm:text-5xl font-normal text-brand-text mb-4">
            The Art of the Loom
          </h2>
          <p className="font-cormorant text-lg text-brand-textMuted italic max-w-2xl mx-auto">
            Every saree is a masterpiece of tradition and technique.
            Discover the stories behind India's most celebrated weaves.
          </p>
        </div>

        {/* Craft stories */}
        <div className="space-y-12">
          {crafts.map((craft, idx) => (
            <div
              key={craft.name}
              className={`flex flex-col ${idx % 2 === 1 ? 'lg:flex-row-reverse' : 'lg:flex-row'} gap-8 lg:gap-12 items-center`}
            >
              {/* Image placeholder */}
              <div className="w-full lg:w-1/2">
                <div className="bg-ivory-300 rounded p-12 flex items-center justify-center min-h-72">
                  <div className="text-center">
                    <span className="text-6xl block mb-4">🥻</span>
                    <p className="text-sm text-brand-textMuted italic font-cormorant">
                      {/* TODO: <img src={imageUrl}> when images provided */}
                      {craft.name} Collection
                    </p>
                  </div>
                </div>
              </div>

              {/* Content */}
              <div className="w-full lg:w-1/2">
                <div className="mb-4 flex items-center gap-2">
                  <div className="h-px bg-gold-600 w-6" />
                  <span className="text-xs font-medium text-gold-600 uppercase tracking-wider">
                    {craft.region}
                  </span>
                </div>

                <h3 className="font-playfair text-3xl font-normal text-brand-text mb-3">
                  {craft.name}
                </h3>

                <p className="text-base text-brand-text leading-relaxed mb-4">
                  {craft.story}
                </p>

                <p className="text-sm text-gold-700 font-medium mb-6">
                  {craft.details}
                </p>

                <Link
                  to={craft.href}
                  className="inline-flex items-center gap-2 text-gold-600 hover:gap-3 transition-all duration-300 group"
                >
                  <span className="text-sm font-medium">Explore {craft.name}</span>
                  <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default CraftStorySection;
