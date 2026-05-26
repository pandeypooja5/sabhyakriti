import { Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
}

const Breadcrumb: React.FC<BreadcrumbProps> = ({ items }) => {
  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-sm text-gray-500 flex-wrap">
      <Link to="/" className="hover:text-saffron-500 transition-colors">
        Home
      </Link>
      {items.map((item, idx) => (
        <span key={idx} className="flex items-center gap-1">
          <ChevronRight className="h-4 w-4 text-gray-400 flex-shrink-0" />
          {item.href && idx < items.length - 1 ? (
            <Link to={item.href} className="hover:text-saffron-500 transition-colors">
              {item.label}
            </Link>
          ) : (
            <span className="text-gray-800 font-medium">{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
};

export default Breadcrumb;
