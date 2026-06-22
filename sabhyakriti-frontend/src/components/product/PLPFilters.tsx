import { useState, useEffect, useRef } from 'react';
import { SlidersHorizontal, ChevronDown, X } from 'lucide-react';
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
    <div className="border-b border-ivory-200 pb-3">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between w-full text-sm font-semibold text-brand-text py-2"
      >
        {title}
        <ChevronDown className={cn('h-4 w-4 transition-transform text-brand-textMuted', open && 'rotate-180')} />
      </button>
      {open && (
        <ul className="space-y-1.5 mt-1">
          {items.map((item) => (
            <li key={item.id}>
              <label className="flex items-center gap-2.5 cursor-pointer group px-1 py-1 rounded hover:bg-ivory-100">
                <input
                  type="checkbox"
                  checked={selected.includes(item.id)}
                  onChange={() => onToggle(item.id)}
                  className="h-4 w-4 rounded border-gray-300 text-gold-600 focus:ring-gold-500 cursor-pointer"
                />
                <span className="text-sm text-brand-text flex-1">{item.name}</span>
                {item.productCount !== undefined && (
                  <span className="text-xs text-brand-textMuted">({item.productCount})</span>
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

const PLPFilters: React.FC<PLPFiltersProps> = () => {
  const dispatch = useAppDispatch();
  const filters = useAppSelector((s) => s.products.filters);
  const [fabrics, setFabrics] = useState<Category[]>([]);
  const [occasions, setOccasions] = useState<Category[]>([]);
  const [regions, setRegions] = useState<Category[]>([]);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listCategories('FABRIC').then(setFabrics).catch(() => null);
    listCategories('OCCASION').then(setOccasions).catch(() => null);
    listCategories('REGION').then(setRegions).catch(() => null);
  }, []);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const totalActive = filters.fabricIds.length + filters.occasionIds.length + filters.regionIds.length;

  return (
    <div ref={ref} className="relative flex-shrink-0" data-testid="plp-filters">
      <button
        onClick={() => setOpen(!open)}
        className={cn(
          'flex items-center gap-2 px-3 py-2 rounded-lg border text-sm font-medium transition-colors',
          totalActive > 0
            ? 'border-gold-600 bg-gold-50 text-gold-700'
            : 'border-ivory-400 bg-white text-brand-text hover:border-gold-400 hover:bg-ivory-100'
        )}
        aria-label="Open filters"
      >
        <SlidersHorizontal className="h-4 w-4" />
        <span>Filters</span>
        {totalActive > 0 && (
          <span className="bg-gold-600 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-semibold">
            {totalActive}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute top-full left-0 mt-2 w-64 bg-white border border-ivory-300 rounded-xl shadow-xl z-40 p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-semibold text-brand-text">Filters</span>
            <div className="flex items-center gap-2">
              {totalActive > 0 && (
                <button
                  onClick={() => dispatch(resetFilters())}
                  className="text-xs text-red-500 hover:text-red-700 font-medium flex items-center gap-1"
                >
                  <X className="h-3 w-3" /> Clear all
                </button>
              )}
              <button onClick={() => setOpen(false)} className="text-brand-textMuted hover:text-brand-text">
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div className="space-y-1 max-h-96 overflow-y-auto">
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
          </div>
        </div>
      )}
    </div>
  );
};

export default PLPFilters;
