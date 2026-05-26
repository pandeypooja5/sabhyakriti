import { Link } from 'react-router-dom';
import { Layers, Calendar, MapPin, ArrowRight } from 'lucide-react';

const shortcuts = [
  {
    icon: Layers,
    title: 'Browse by Fabric',
    description: 'Silk, Cotton, Georgette, Banarasi & more',
    href: '/sarees?filterBy=fabric',
    color: 'from-amber-500 to-orange-500',
    testId: 'shortcut-fabric',
  },
  {
    icon: Calendar,
    title: 'Browse by Occasion',
    description: 'Wedding, Festival, Party, Casual & office wear',
    href: '/sarees?filterBy=occasion',
    color: 'from-teal-600 to-teal-800',
    testId: 'shortcut-occasion',
  },
  {
    icon: MapPin,
    title: 'Browse by Region',
    description: 'Bengal, Rajasthan, Tamil Nadu, Gujarat & more',
    href: '/sarees?filterBy=region',
    color: 'from-purple-600 to-purple-800',
    testId: 'shortcut-region',
  },
];

const CategoryShortcuts: React.FC = () => {
  return (
    <section className="py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto" data-testid="category-shortcuts">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Explore Our Collection</h2>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {shortcuts.map(({ icon: Icon, title, description, href, color, testId }) => (
          <Link
            key={title}
            to={href}
            data-testid={testId}
            className={`group relative overflow-hidden rounded-2xl bg-gradient-to-br ${color} text-white p-6 hover:scale-[1.02] transition-transform duration-200 shadow-md hover:shadow-lg`}
          >
            <div className="flex items-start justify-between mb-4">
              <div className="h-12 w-12 rounded-xl bg-white/20 flex items-center justify-center">
                <Icon className="h-6 w-6" />
              </div>
              <ArrowRight className="h-5 w-5 opacity-60 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
            </div>
            <h3 className="text-lg font-bold mb-1">{title}</h3>
            <p className="text-sm opacity-80">{description}</p>
            <div className="absolute -bottom-4 -right-4 h-20 w-20 rounded-full bg-white/10" />
          </Link>
        ))}
      </div>
    </section>
  );
};

export default CategoryShortcuts;
