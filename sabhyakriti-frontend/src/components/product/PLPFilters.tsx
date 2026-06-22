import { useState, useEffect, useRef } from 'react';
import { ChevronDown, X, SlidersHorizontal } from 'lucide-react';
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

interface DropdownProps {
  label: string;
  items: Category[];
  selected: string[];
  onToggle: (id: string) => void;
}

const FilterDropdown: React.FC<DropdownProps> = ({ label, items, selected, onToggle }) => {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const activeCount = selected.length;

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className={cn(
          'flex items-center gap-2 px-4 py-2 rounded-full border text-sm font-medium transition-colors',
          activeCount > 0
            ? 'border-gold-600 bg-gold-50 text-gold-700'
            : 'border-ivory-400 bg-white text-brand-text hover:border-gold-400 hover:bg-ivory-100'
        )}
      >
        {label}
        {activeCount > 0 && (
          <span className="bg-gold-600 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-semibold">
            {activeCount}
          </span>
        )}
        <ChevronDown className={cn('h-4 w-4 transition-transform', open && 'rotate-180')} />
      </button>

      {open && (
        <div className="absolute top-full left-0 mt-2 w-56 bg-white border border-ivory-300 rounded-xl shadow-lg z-40 p-3">
          <p className="text-xs font-semibold text-brand-textMuted uppercase tracking-wide mb-2 px-1">{label}</p>
          <ul className="space-y-1 max-h-64 overflow-y-auto">
            {items.map((item) => (
              <li key={item.id}>
                <label className="flex items-center gap-2.5 cursor-pointer group px-1 py-1.5 rounded hover:bg-ivory-100">
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
        </div>
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

  useEffect(() => {
    listCategories('FABRIC').then(setFabrics).catch(() => null);
    listCategories('OCCASION').then(setOccasions).catch(() => null);
    listCategories('REGION').then(setRegions).catch(() => null);
  }, []);

  const totalActive = filters.fabricIds.length + filters.occasionIds.length + filters.regionIds.length;

  return (
    <div className="flex items-center gap-2 flex-wrap" data-testid="plp-filters">
      <div className="flex items-center gap-1.5 text-sm font-medium text-brand-textMuted mr-1">
        <SlidersHorizontal className="h-4 w-4" />
        <span>Filter:</span>
      </div>

      {fabrics.length > 0 && (
        <FilterDropdown
          label="Fabric"
          items={fabrics}
          selected={filters.fabricIds}
          onToggle={(id) => dispatch(toggleFabricFilter(id))}
        />
      )}
      {occasions.length > 0 && (
        <FilterDropdown
          label="Occasion"
          items={occasions}
          selected={filters.occasionIds}
          onToggle={(id) => dispatch(toggleOccasionFilter(id))}
        />
      )}
      {regions.length > 0 && (
        <FilterDropdown
          label="Region"
          items={regions}
          selected={filters.regionIds}
          onToggle={(id) => dispatch(toggleRegionFilter(id))}
        />
      )}

      {totalActive > 0 && (
        <button
          onClick={() => dispatch(resetFilters())}
          data-testid="filters-clear-all"
          className="flex items-center gap-1 px-3 py-2 text-sm text-red-500 hover:text-red-700 font-medium rounded-full border border-red-200 hover:bg-red-50 transition-colors"
        >
          <X className="h-3.5 w-3.5" /> Clear all
        </button>
      )}
    </div>
  );
};

export default PLPFilters;
