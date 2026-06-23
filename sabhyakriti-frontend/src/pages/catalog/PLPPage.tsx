import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { useAppDispatch, useAppSelector } from '@/store/store';
import { fetchProducts, setFilters, setSearch, setSort, setPage } from '@/store/slices/productSlice';
import type { ProductFilters } from '@/types';
import PLPFilters from '@/components/product/PLPFilters';
import PLPSearch from '@/components/product/PLPSearch';
import PLPSort from '@/components/product/PLPSort';
import ProductGrid from '@/components/product/ProductGrid';
import PLPPagination from '@/components/product/PLPPagination';

const PLPPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const [searchParams, setSearchParams] = useSearchParams();
  const { products, total, loading, filters, search, sort, page, pageSize } = useAppSelector((s) => s.products);
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
      <Helmet>
        <title>Buy Handcrafted Sarees Online — Lehariya, Bandhani, Silk & More | Sabhyakriti</title>
        <meta name="description" content="Shop authentic handcrafted sarees at Sabhyakriti. Browse lehariya, bandhani, silk, chiffon & georgette sarees for weddings, festivals & parties. Free pan-India shipping." />
        <meta name="keywords" content="buy sarees online, lehariya sarees, bandhani sarees, silk sarees, banarasi sarees, linen sarees, tissue sarees, organza sarees, chiffon sarees, georgette sarees, Rajasthani sarees, wedding sarees, festive sarees, Jaipur sarees, gotta patti sarees, traditional Indian sarees" />
        <link rel="canonical" href="https://www.sabhyakriti.com/" />
      </Helmet>

      {/* Search + filter icon + sort */}
      <div className="flex items-center gap-3 mb-6">
        <PLPFilters />
        <div className="flex-1">
          <PLPSearch />
        </div>
        <PLPSort />
      </div>

      {/* Products */}
      <ProductGrid products={products} loading={loading} total={total} />
      <PLPPagination />
    </div>
  );
};

export default PLPPage;
