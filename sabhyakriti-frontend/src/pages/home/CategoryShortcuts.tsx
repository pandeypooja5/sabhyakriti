import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

const shortcuts = [
  {
    ornament: '✦',
    title: 'By Craft',
    description: 'Banarasi Silk, Kanjivaram, Jamdani & traditional weaves',
    href: '/sarees?filterBy=fabric',
    testId: 'shortcut-craft',
  },
  {
    ornament: '◈',
    title: 'By Occasion',
    description: 'Wedding, Festive, Party, Casual & professional sarees',
    href: '/sarees?filterBy=occasion',
    testId: 'shortcut-occasion',
  },
  {
    ornament: '❧',
    title: 'By Heritage Region',
    description: 'Bengal, Varanasi, Kanchipuram, Rajasthan & more',
    href: '/sarees?filterBy=region',
    testId: 'shortcut-region',
  },
];

const CategoryShortcuts: React.FC = () => {
  return (
    <div className="w-full max-w-lg" data-testid="category-shortcuts">
      {/* Header */}
      <div className="text-center mb-8">
        <p className="font-cormorant text-sm text-gold-600 italic tracking-widest uppercase mb-2">
          Explore by
        </p>
        <h2 className="font-playfair text-3xl sm:text-4xl font-normal text-brand-text mb-3">
          The World of SabhyaKriti
        </h2>
        <div className="flex items-center justify-center gap-2">
          <div className="h-px bg-gold-600 w-6" />
          <span className="text-gold-600 text-sm">✦</span>
          <div className="h-px bg-gold-600 w-6" />
        </div>
      </div>

      {/* Cards grid */}
      <div className="space-y-4">
        {shortcuts.map(({ ornament, title, description, href, testId }) => (
          <Link
            key={title}
            to={href}
            data-testid={testId}
            className="group relative border-2 border-ivory-400 hover:border-gold-500 bg-white rounded p-6 transition-all duration-300 hover:shadow-[0_4px_20px_rgba(201,160,66,0.12)]"
          >
            {/* Ornate gold filigree corners */}
            {/* Top-left corner */}
            <div className="absolute top-2 left-2 w-4 h-4">
              <svg viewBox="0 0 24 24" className="w-full h-full text-gold-500 opacity-60">
                <path
                  fill="currentColor"
                  d="M3 3h4v2H5v2H3V3m16 0h4v4h-2V5h-2V3m-4 20h4v2h-4v-2m8-2v2h2v-4h-2v2m-16-2h2v4h-2v-2h-2v-2h2z"
                />
              </svg>
            </div>

            {/* Top-right corner */}
            <div className="absolute top-2 right-2 w-4 h-4">
              <svg viewBox="0 0 24 24" className="w-full h-full text-gold-500 opacity-60 scale-x-[-1]">
                <path
                  fill="currentColor"
                  d="M3 3h4v2H5v2H3V3m16 0h4v4h-2V5h-2V3m-4 20h4v2h-4v-2m8-2v2h2v-4h-2v2m-16-2h2v4h-2v-2h-2v-2h2z"
                />
              </svg>
            </div>

            {/* Bottom-left corner */}
            <div className="absolute bottom-2 left-2 w-4 h-4">
              <svg viewBox="0 0 24 24" className="w-full h-full text-gold-500 opacity-60 scale-y-[-1]">
                <path
                  fill="currentColor"
                  d="M3 3h4v2H5v2H3V3m16 0h4v4h-2V5h-2V3m-4 20h4v2h-4v-2m8-2v2h2v-4h-2v2m-16-2h2v4h-2v-2h-2v-2h2z"
                />
              </svg>
            </div>

            {/* Bottom-right corner */}
            <div className="absolute bottom-2 right-2 w-4 h-4">
              <svg viewBox="0 0 24 24" className="w-full h-full text-gold-500 opacity-60 scale-[-1]">
                <path
                  fill="currentColor"
                  d="M3 3h4v2H5v2H3V3m16 0h4v4h-2V5h-2V3m-4 20h4v2h-4v-2m8-2v2h2v-4h-2v2m-16-2h2v4h-2v-2h-2v-2h2z"
                />
              </svg>
            </div>

            {/* Ornament icon */}
            <div className="h-8 w-8 flex items-center justify-center bg-gold-100 rounded mb-3">
              <span className="text-sm text-gold-600">{ornament}</span>
            </div>

            {/* Content */}
            <h3 className="font-playfair text-xl font-normal text-brand-text mb-1">
              {title}
            </h3>
            <p className="text-xs text-brand-textMuted leading-relaxed mb-3">
              {description}
            </p>

            {/* CTA arrow */}
            <div className="flex items-center gap-1 text-gold-600 group-hover:gap-2 transition-all duration-300">
              <span className="text-xs font-medium">Explore</span>
              <ArrowRight className="h-3 w-3 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default CategoryShortcuts;
