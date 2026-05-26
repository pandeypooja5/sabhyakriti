import { useState, useEffect, useCallback } from 'react';
import { Search, X } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '@/store/store';
import { setSearch } from '@/store/slices/productSlice';

const PLPSearch: React.FC = () => {
  const dispatch = useAppDispatch();
  const searchValue = useAppSelector((s) => s.products.search);
  const [localValue, setLocalValue] = useState(searchValue);

  // Debounce 300ms
  const debounced = useCallback(
    (() => {
      let timer: ReturnType<typeof setTimeout>;
      return (val: string) => {
        clearTimeout(timer);
        timer = setTimeout(() => dispatch(setSearch(val)), 300);
      };
    })(),
    [dispatch]
  );

  useEffect(() => {
    debounced(localValue);
  }, [localValue, debounced]);

  const handleClear = () => {
    setLocalValue('');
    dispatch(setSearch(''));
  };

  return (
    <div className="relative" data-testid="plp-search">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
      <input
        type="search"
        value={localValue}
        onChange={(e) => setLocalValue(e.target.value)}
        placeholder="Search sarees..."
        data-testid="plp-search-input"
        className="w-full pl-9 pr-8 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-saffron-500 focus:border-transparent"
      />
      {localValue && (
        <button
          onClick={handleClear}
          data-testid="plp-search-clear"
          className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
          aria-label="Clear search"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      )}
    </div>
  );
};

export default PLPSearch;
