import { useAppDispatch, useAppSelector } from '@/store/store';
import { setSort } from '@/store/slices/productSlice';
import type { ProductFilters } from '@/types';

const sortOptions: { value: ProductFilters['sort']; label: string }[] = [
  { value: 'newest', label: 'Newest First' },
  { value: 'price_asc', label: 'Price: Low to High' },
  { value: 'price_desc', label: 'Price: High to Low' },
  { value: 'rating', label: 'Highest Rated' },
  { value: 'popularity', label: 'Most Popular' },
];

const PLPSort: React.FC = () => {
  const dispatch = useAppDispatch();
  const sort = useAppSelector((s) => s.products.sort);

  return (
    <div className="flex items-center gap-2" data-testid="plp-sort">
      <label htmlFor="plp-sort-select" className="text-sm text-gray-600 whitespace-nowrap">
        Sort by:
      </label>
      <select
        id="plp-sort-select"
        value={sort}
        onChange={(e) => dispatch(setSort(e.target.value as ProductFilters['sort']))}
        data-testid="plp-sort-select"
        className="text-sm border border-gray-300 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-saffron-500 bg-white"
      >
        {sortOptions.map((opt) => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  );
};

export default PLPSort;
