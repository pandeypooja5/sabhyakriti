import { useState, useEffect } from 'react';
import { ChevronDown, X } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '@/store/store';
import {
  toggleFabricFilter,
  toggleOccasionFilter,
  toggleRegionFilter,
  resetFilters,
} from '@/store/slices/productSlice';
import { listCategories } from '@/services/productService';
import type { Category } from '@/types';
import { cn } from '@/lib/utils';

interface FilterSectionProps {
  title: string;
  items: Category[];
  selected: string[];
  onToggle: (id: string) => void;
}

const FilterSection: React.FC<FilterSectionProps> = ({ title, items, selected, onToggle }) => {
  const [open, setOpen] = useState(true);

  return (
    <div className="border-b border-ivory-300 py-3">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between w-full text-sm font-semibold text-brand-text py-1"
        data-testid={`filter-section-${title.toLowerCase()}`}
      >
        {title}
        <ChevronDown className={cn('h-4 w-4 transition-transform', open && 'rotate-180')} />
      </button>
      {open && (
        <ul className="mt-2 space-y-1.5">
          {items.map((item) => (
            <li key={item.id}>
              <label className="flex items-center gap-2.5 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={selected.includes(item.id)}
                  onChange={() => onToggle(item.id)}
                  data-testid={`filter-${item.slug}`}
                  className="h-4 w-4 rounded border-gold-600 text-gold-600 focus:ring-gold-600 cursor-pointer"
                />
                <span className="text-sm text-brand-text group-hover:text-brand-text">
                  {item.name}
                </span>
                {item.productCount !== undefined && (
                  <span className="text-xs text-brand-textMuted ml-auto">({item.productCount})</span>
                )}
              </label>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

interface PLPFiltersProps {
  onClose?: () => void;
}

const PLPFilters: React.FC<PLPFiltersProps> = ({ onClose }) => {
  const dispatch = useAppDispatch();
  const filters = useAppSelector((s) => s.products.filters);
  const [fabrics, setFabrics] = useState<Category[]>([]);
  const [occasions, setOccasions] = useState<Category[]>([]);
  const [regions, setRegions] = useState<Category[]>([]);

  useEffect(() => {
    listCategories('FABRIC').then(setFabrics).catch(() => null);
    listCategories('OCCASION').then(setOccasions).catch(() => null);
    listCategories('REGION').then(setRegions).catch(() => null);
  }, []);

  const totalActive = filters.fabricIds.length + filters.occasionIds.length + filters.regionIds.length;

  return (
    <aside
      className="w-full bg-ivory-100 rounded border border-ivory-400 p-4"
      data-testid="plp-filters"
    >
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-base font-semibold text-brand-text">
          Filters {totalActive > 0 && <span className="ml-1 text-xs bg-gold-100 text-gold-600 px-1.5 py-0.5 rounded-full">{totalActive}</span>}
        </h2>
        <div className="flex items-center gap-2">
          {totalActive > 0 && (
            <button
              onClick={() => dispatch(resetFilters())}
              data-testid="filters-clear-all"
              className="text-xs text-red-500 hover:text-red-700 font-medium flex items-center gap-1"
            >
              <X className="h-3 w-3" /> Clear All
            </button>
          )}
          {onClose && (
            <button onClick={onClose} className="text-brand-textMuted hover:text-brand-text">
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {fabrics.length > 0 && (
        <FilterSection
          title="Fabric"
          items={fabrics}
          selected={filters.fabricIds}
          onToggle={(id) => dispatch(toggleFabricFilter(id))}
        />
      )}
      {occasions.length > 0 && (
        <FilterSection
          title="Occasion"
          items={occasions}
          selected={filters.occasionIds}
          onToggle={(id) => dispatch(toggleOccasionFilter(id))}
        />
      )}
      {regions.length > 0 && (
        <FilterSection
          title="Region"
          items={regions}
          selected={filters.regionIds}
          onToggle={(id) => dispatch(toggleRegionFilter(id))}
        />
      )}
    </aside>
  );
};

export default PLPFilters;
