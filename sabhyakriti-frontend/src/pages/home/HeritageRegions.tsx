import { Link } from 'react-router-dom';

const regions = [
  {
    name: 'Bengal',
    emoji: '🌙',
    description: 'Jamdani, Muslin, Tant',
    href: '/sarees?region=bengal',
  },
  {
    name: 'Varanasi',
    emoji: '✨',
    description: 'Banarasi Silk, Gold Zari',
    href: '/sarees?region=varanasi',
  },
  {
    name: 'Kanchipuram',
    emoji: '👑',
    description: 'Kanjivaram Silk, Pure Silk',
    href: '/sarees?region=kanchipuram',
  },
  {
    name: 'Rajasthan',
    emoji: '🌞',
    description: 'Bandhani, Leheriya, Prints',
    href: '/sarees?region=rajasthan',
  },
  {
    name: 'Odisha',
    emoji: '🎭',
    description: 'Sambalpuri, Ikat, Patterns',
    href: '/sarees?region=odisha',
  },
  {
    name: 'Gujarat',
    emoji: '🔶',
    description: 'Patola, Bandhani, Colors',
    href: '/sarees?region=gujarat',
  },
];

const HeritageRegions: React.FC = () => {
  return (
    <section className="py-16 px-4 sm:px-6 lg:px-8 bg-ivory-200" data-testid="heritage-regions">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-16">
          <p className="font-cormorant text-sm text-gold-600 italic tracking-widest uppercase mb-2">
            Across India
          </p>
          <h2 className="font-playfair text-4xl sm:text-5xl font-normal text-brand-text mb-4">
            Journey Through the Regions
          </h2>
          <p className="font-cormorant text-lg text-brand-textMuted italic max-w-2xl mx-auto">
            From the looms of Bengal to the silks of Tamil Nadu,
            explore the diverse heritage regions of Indian saree weaving.
          </p>
        </div>

        {/* Region grid - asymmetric layout */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {regions.map((region, idx) => (
            <Link
              key={region.name}
              to={region.href}
              className={`group relative overflow-hidden rounded border-2 border-ivory-400 hover:border-gold-600 transition-all duration-300 p-8 flex flex-col items-center justify-center text-center min-h-48 hover:shadow-[0_4px_20px_rgba(201,160,66,0.12)] bg-ivory-100 ${
                idx === 0 ? 'sm:col-span-2 lg:col-span-1' : ''
              }`}
            >
              {/* Corner bracket decoration */}
              <div className="absolute top-2 left-2 w-4 h-4 border-t-2 border-l-2 border-gold-600/40" />
              <div className="absolute bottom-2 right-2 w-4 h-4 border-b-2 border-r-2 border-gold-600/40" />

              {/* Content */}
              <span className="text-5xl mb-3">{region.emoji}</span>
              <h3 className="font-playfair text-2xl font-normal text-brand-text mb-1 group-hover:text-gold-600 transition-colors">
                {region.name}
              </h3>
              <p className="text-xs text-brand-textMuted font-medium tracking-widest uppercase">
                {region.description}
              </p>

              {/* Hover indicator */}
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-gold-600 to-transparent group-hover:h-1 transition-all duration-300" />
            </Link>
          ))}
        </div>

        {/* Footer text */}
        <div className="text-center mt-12">
          <p className="font-cormorant text-base text-brand-textMuted italic">
            Each region brings its own unique weaving tradition and artistic excellence.
          </p>
        </div>
      </div>
    </section>
  );
};

export default HeritageRegions;
