import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ChevronDown } from 'lucide-react';

const categories = [
  {
    label: 'All Sarees',
    href: '/sarees',
    dropdown: null,
  },
  {
    label: 'By Craft',
    href: '/sarees?fabricIds=',
    dropdown: [
      { label: 'Silk', href: '/sarees?fabric=silk' },
      { label: 'Cotton', href: '/sarees?fabric=cotton' },
      { label: 'Georgette', href: '/sarees?fabric=georgette' },
      { label: 'Chiffon', href: '/sarees?fabric=chiffon' },
      { label: 'Linen', href: '/sarees?fabric=linen' },
      { label: 'Banarasi', href: '/sarees?fabric=banarasi' },
      { label: 'Kanjivaram', href: '/sarees?fabric=kanjivaram' },
    ],
  },
  {
    label: 'By Occasion',
    href: '/sarees?occasionIds=',
    dropdown: [
      { label: 'Wedding', href: '/sarees?occasion=wedding' },
      { label: 'Festival', href: '/sarees?occasion=festival' },
      { label: 'Party Wear', href: '/sarees?occasion=party' },
      { label: 'Casual', href: '/sarees?occasion=casual' },
      { label: 'Office Wear', href: '/sarees?occasion=office' },
    ],
  },
  {
    label: 'By Heritage Region',
    href: '/sarees?regionIds=',
    dropdown: [
      { label: 'Bengal', href: '/sarees?region=bengal' },
      { label: 'Rajasthan', href: '/sarees?region=rajasthan' },
      { label: 'Tamil Nadu', href: '/sarees?region=tamil-nadu' },
      { label: 'Gujarat', href: '/sarees?region=gujarat' },
      { label: 'Odisha', href: '/sarees?region=odisha' },
      { label: 'Assam', href: '/sarees?region=assam' },
    ],
  },
];

const CategoryNav: React.FC = () => {
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);

  return (
    <nav className="hidden md:block bg-ivory-200 border-b border-ivory-400" data-testid="category-nav">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <ul className="flex items-center gap-0">
          {categories.map((cat) => (
            <li
              key={cat.label}
              className="relative"
              onMouseEnter={() => setActiveDropdown(cat.label)}
              onMouseLeave={() => setActiveDropdown(null)}
            >
              <Link
                to={cat.href}
                className="relative flex items-center gap-1 px-4 py-3 text-sm font-medium text-[#7A6050] hover:text-gold-700 transition-colors whitespace-nowrap after:content-[''] after:absolute after:bottom-0 after:left-0 after:h-0.5 after:bg-gold-600 after:w-full after:scale-x-0 after:origin-left after:transition-transform after:duration-200 hover:after:scale-x-100"
                data-testid={`nav-${cat.label.toLowerCase().replace(/ /g, '-')}`}
              >
                {cat.label}
                {cat.dropdown && <ChevronDown className="h-3.5 w-3.5" />}
              </Link>

              {cat.dropdown && activeDropdown === cat.label && (
                <div className="absolute left-0 top-full w-48 bg-ivory-100 text-brand-text shadow-lg rounded z-50 py-1 border border-ivory-400">
                  {cat.dropdown.map((item) => (
                    <Link
                      key={item.label}
                      to={item.href}
                      className="block px-4 py-2 text-sm text-brand-text hover:bg-gold-50 hover:text-gold-700 transition-colors"
                      data-testid={`nav-dropdown-${item.label.toLowerCase().replace(/ /g, '-')}`}
                    >
                      {item.label}
                    </Link>
                  ))}
                </div>
              )}
            </li>
          ))}
          <li className="ml-auto">
            <Link
              to="/sarees?sort=newest"
              className="flex items-center px-4 py-3 text-sm font-medium text-burgundy-500 hover:text-gold-700 transition-colors"
              data-testid="nav-new-arrivals"
            >
              New Arrivals
            </Link>
          </li>
        </ul>
      </div>
    </nav>
  );
};

export default CategoryNav;
