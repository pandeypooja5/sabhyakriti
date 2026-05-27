const artisans = [
  {
    name: 'Ramkali Devi',
    craft: 'Master Weaver',
    village: 'Varanasi, Uttar Pradesh',
    quote:
      '"Weaving is not just my profession; it is my family\'s legacy. Every thread I use carries the prayers and blessings of generations."',
  },
  {
    name: 'Sunderamma',
    craft: 'Silk Artisan',
    village: 'Kanchipuram, Tamil Nadu',
    quote:
      '"The beauty of a saree lies not just in its appearance, but in the patience and love we pour into every inch of it."',
  },
  {
    name: 'Suresh Debnath',
    craft: 'Jamdani Specialist',
    village: 'Dhaka (Bengal)',
    quote:
      '"When someone wears a saree I\'ve created, they carry a piece of our heritage and our hearts with them."',
  },
];

const ArtisanSection: React.FC = () => {
  return (
    <section
      className="py-16 px-4 sm:px-6 lg:px-8 bg-[#1C110A] text-ivory-400"
      data-testid="artisan-section"
    >
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-16">
          <p className="font-cormorant text-sm text-gold-500 italic tracking-widest uppercase mb-2">
            Meet the Masters
          </p>
          <h2 className="font-playfair text-4xl sm:text-5xl font-normal text-ivory-100 mb-4">
            Hands That Weave History
          </h2>
          <p className="font-cormorant text-lg text-ivory-400 italic max-w-2xl mx-auto">
            Behind every SabhyaKriti saree is a master artisan whose skill,
            dedication, and passion for the craft is unparalleled.
          </p>
        </div>

        {/* Artisan cards grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {artisans.map((artisan) => (
            <div
              key={artisan.name}
              className="flex flex-col items-center text-center p-8 border border-ivory-700/30 rounded hover:border-gold-600/50 transition-colors"
            >
              {/* Initial circle */}
              <div className="h-20 w-20 rounded-full bg-gradient-to-br from-gold-600 to-gold-700 flex items-center justify-center mb-6">
                <span className="text-3xl font-playfair font-bold text-white">
                  {artisan.name[0]}
                </span>
              </div>

              {/* Quote */}
              <blockquote className="font-cormorant text-base text-ivory-200 italic mb-6 leading-relaxed">
                {artisan.quote}
              </blockquote>

              {/* Details */}
              <h3 className="font-playfair text-xl font-normal text-ivory-100 mb-1">
                {artisan.name}
              </h3>
              <p className="text-sm text-gold-500 font-medium mb-2">{artisan.craft}</p>
              <p className="text-xs text-ivory-600">{artisan.village}</p>
            </div>
          ))}
        </div>

        {/* CTA */}
        <div className="text-center mt-12">
          <p className="font-cormorant text-lg text-ivory-400 italic">
            Every saree purchased supports these artisans and their communities.
          </p>
        </div>
      </div>
    </section>
  );
};

export default ArtisanSection;
