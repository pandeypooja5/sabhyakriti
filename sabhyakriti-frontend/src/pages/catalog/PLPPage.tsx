import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { SlidersHorizontal, X } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '@/store/store';
import { fetchProducts, setFilters, setSearch, setSort, setPage } from '@/store/slices/productSlice';
import type { ProductFilters } from '@/types';
import PLPFilters from '@/components/product/PLPFilters';
import PLPSearch from '@/components/product/PLPSearch';
import PLPSort from '@/components/product/PLPSort';
import ProductGrid from '@/components/product/ProductGrid';
import PLPPagination from '@/components/product/PLPPagination';
import Breadcrumb from '@/components/shared/Breadcrumb';

const PLPPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const [searchParams, setSearchParams] = useSearchParams();
  const { products, total, loading, filters, search, sort, page, pageSize } = useAppSelector((s) => s.products);
  const [filtersOpen, setFiltersOpen] = useState(false);

  // Sync URL → Redux on mount
  useEffect(() => {
    const urlSearch = searchParams.get('search') ?? '';
    const urlSort = (searchParams.get('sort') ?? 'newest') as ProductFilters['sort'];
    const urlPage = parseInt(searchParams.get('page') ?? '1');
    if (urlSearch) dispatch(setSearch(urlSearch));
    if (urlSort) dispatch(setSort(urlSort));
    if (urlPage > 1) dispatch(setPage(urlPage));
  }, []);

  // Sync Redux → fetch
  useEffect(() => {
    const params: ProductFilters = {
      ...filters,
      search: search || undefined,
      sort,
      page,
      pageSize,
    };
    dispatch(fetchProducts(params));

    // Update URL
    const newParams = new URLSearchParams();
    if (search) newParams.set('search', search);
    if (sort !== 'newest') newParams.set('sort', sort ?? 'newest');
    if (page > 1) newParams.set('page', String(page));
    if (filters.fabricIds.length) newParams.set('fabricIds', filters.fabricIds.join(','));
    if (filters.occasionIds.length) newParams.set('occasionIds', filters.occasionIds.join(','));
    if (filters.regionIds.length) newParams.set('regionIds', filters.regionIds.join(','));
    setSearchParams(newParams);
  }, [dispatch, filters, search, sort, page, pageSize]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6" data-testid="plp-page">
        <Breadcrumb items={[{ label: 'Sarees' }]} />

        <div className="flex items-center gap-4 mt-4 mb-6">
          {/* Filters Menu Icon */}
          <button
            onClick={() => setFiltersOpen(true)}
            className="flex items-center p-2 text-brand-text hover:bg-ivory-200 rounded transition-colors"
            data-testid="mobile-filters-btn"
            aria-label="Open filters"
          >
            <SlidersHorizontal className="h-5 w-5" />
          </button>

          <h1 className="text-2xl font-playfair font-normal text-brand-text flex-1">All Sarees</h1>
        </div>

        {/* Top bar: search + sort */}
        <div className="flex flex-col sm:flex-row gap-3 mb-6">
          <div className="flex-1">
            <PLPSearch />
          </div>
          <PLPSort />
        </div>

      <div className="flex gap-6">
        {/* Desktop filters sidebar */}
        <div className="hidden lg:block w-56 flex-shrink-0">
          <PLPFilters />
        </div>

        {/* Mobile filters overlay */}
        {filtersOpen && (
          <div className="fixed inset-0 z-50 lg:hidden">
            <div className="absolute inset-0 bg-black/50" onClick={() => setFiltersOpen(false)} />
            <div className="absolute right-0 inset-y-0 w-72 bg-ivory-100 shadow-xl overflow-y-auto p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-brand-text">Filters</h2>
                <button onClick={() => setFiltersOpen(false)} className="text-brand-textMuted hover:text-brand-text">
                  <X className="h-5 w-5" />
                </button>
              </div>
              <PLPFilters onClose={() => setFiltersOpen(false)} />
            </div>
          </div>
        )}

        {/* Products */}
        <div className="flex-1 min-w-0">
          <ProductGrid products={products} loading={loading} total={total} />
          <PLPPagination />
        </div>
      </div>
    </div>
  );
};

export default PLPPage;
