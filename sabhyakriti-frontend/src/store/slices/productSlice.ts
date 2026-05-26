import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import type { Product, ProductFilters } from '@/types';
import * as productService from '@/services/productService';

interface ProductState {
  products: Product[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  filters: {
    fabricIds: string[];
    occasionIds: string[];
    regionIds: string[];
    minPrice?: number;
    maxPrice?: number;
    inStock?: boolean;
  };
  search: string;
  sort: ProductFilters['sort'];
  loading: boolean;
  error: string | null;
}

const initialState: ProductState = {
  products: [],
  total: 0,
  page: 1,
  pageSize: 20,
  totalPages: 0,
  filters: {
    fabricIds: [],
    occasionIds: [],
    regionIds: [],
  },
  search: '',
  sort: 'newest',
  loading: false,
  error: null,
};

export const fetchProducts = createAsyncThunk(
  'products/fetchProducts',
  async (filters: ProductFilters, { rejectWithValue }) => {
    try {
      return await productService.listProducts(filters);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      return rejectWithValue(error.response?.data?.message ?? 'Failed to fetch products');
    }
  }
);

const productSlice = createSlice({
  name: 'products',
  initialState,
  reducers: {
    setFilters(state, action: PayloadAction<Partial<ProductState['filters']>>) {
      state.filters = { ...state.filters, ...action.payload };
      state.page = 1;
    },
    setSearch(state, action: PayloadAction<string>) {
      state.search = action.payload;
      state.page = 1;
    },
    setSort(state, action: PayloadAction<ProductFilters['sort']>) {
      state.sort = action.payload;
      state.page = 1;
    },
    setPage(state, action: PayloadAction<number>) {
      state.page = action.payload;
    },
    resetFilters(state) {
      state.filters = { fabricIds: [], occasionIds: [], regionIds: [] };
      state.search = '';
      state.sort = 'newest';
      state.page = 1;
    },
    toggleFabricFilter(state, action: PayloadAction<string>) {
      const id = action.payload;
      const idx = state.filters.fabricIds.indexOf(id);
      if (idx >= 0) state.filters.fabricIds.splice(idx, 1);
      else state.filters.fabricIds.push(id);
      state.page = 1;
    },
    toggleOccasionFilter(state, action: PayloadAction<string>) {
      const id = action.payload;
      const idx = state.filters.occasionIds.indexOf(id);
      if (idx >= 0) state.filters.occasionIds.splice(idx, 1);
      else state.filters.occasionIds.push(id);
      state.page = 1;
    },
    toggleRegionFilter(state, action: PayloadAction<string>) {
      const id = action.payload;
      const idx = state.filters.regionIds.indexOf(id);
      if (idx >= 0) state.filters.regionIds.splice(idx, 1);
      else state.filters.regionIds.push(id);
      state.page = 1;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchProducts.pending, (state) => { state.loading = true; state.error = null; })
      .addCase(fetchProducts.fulfilled, (state, action) => {
        const p = action.payload as Record<string, unknown>;
        state.loading = false;
        // API returns { items, total_count, total_pages, page } or { data, total, totalPages, page }
        state.products = (p.items ?? p.data ?? []) as typeof state.products;
        state.total = (p.total_count ?? p.total ?? 0) as number;
        state.totalPages = (p.total_pages ?? p.totalPages ?? 1) as number;
        state.page = (p.page ?? 1) as number;
      })
      .addCase(fetchProducts.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const {
  setFilters,
  setSearch,
  setSort,
  setPage,
  resetFilters,
  toggleFabricFilter,
  toggleOccasionFilter,
  toggleRegionFilter,
} = productSlice.actions;
export default productSlice.reducer;
