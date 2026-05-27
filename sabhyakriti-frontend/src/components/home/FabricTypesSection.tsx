import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

interface Fabric {
  name: string;
  href: string;
}

const fabrics: Fabric[] = [
  { name: 'Bandhani', href: '/sarees?fabric=bandhani' },
  { name: 'Lehriya', href: '/sarees?fabric=lehriya' },
  { name: 'Chiffon', href: '/sarees?fabric=chiffon' },
  { name: 'Georgette', href: '/sarees?fabric=georgette' },
  { name: 'Gajji Silk', href: '/sarees?fabric=gajji-silk' },
];

const FabricTypesSection: React.FC = () => {
  return (
    <div className="w-full bg-ivory-50 py-12 px-4 sm:px-6 lg:px-8 border-t border-gold-200">
      <div className="max-w-5xl mx-auto">
        {/* Section Title */}
        <p className="text-center font-cormorant text-sm italic text-gold-600 mb-3 tracking-wide">
          Explore by Fabric
        </p>

        {/* Fabric Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
          {fabrics.map((fabric) => (
            <Link
              key={fabric.name}
              to={fabric.href}
              className="group flex flex-col items-center justify-center p-4 sm:p-6 rounded-lg bg-white border border-ivory-300 hover:border-gold-500 hover:shadow-md transition-all duration-300"
            >
              <span className="font-playfair text-lg sm:text-xl font-normal text-brand-text mb-2 text-center">
                {fabric.name}
              </span>
              <ArrowRight className="h-4 w-4 text-gold-600 opacity-0 group-hover:opacity-100 transition-opacity" />
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};

export default FabricTypesSection;
