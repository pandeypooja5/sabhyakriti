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
    <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-sm text-brand-textMuted flex-wrap">
      <Link to="/" className="hover:text-gold-600 transition-colors">
        Home
      </Link>
      {items.map((item, idx) => (
        <span key={idx} className="flex items-center gap-1">
          <ChevronRight className="h-4 w-4 text-brand-textMuted flex-shrink-0" />
          {item.href && idx < items.length - 1 ? (
            <Link to={item.href} className="hover:text-gold-600 transition-colors">
              {item.label}
            </Link>
          ) : (
            <span className="text-brand-text font-medium">{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
};

export default Breadcrumb;
