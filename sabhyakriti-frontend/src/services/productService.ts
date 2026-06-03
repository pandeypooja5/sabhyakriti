import apiClient from './apiClient';
import type { Product, Category, ProductFilters, PaginatedResponse, ProductImage, StockStatus } from '@/types';

// ─── Normalizers: API snake_case → frontend camelCase ─────────────────────────

function normalizeImage(raw: Record<string, unknown>): ProductImage {
  return {
    id: String(raw.image_id ?? raw.id ?? ''),
    url: String(raw.cloudfront_url ?? raw.url ?? '/placeholder.jpg'),
    altText: String(raw.alt_text ?? raw.altText ?? ''),
    isPrimary: Boolean(raw.is_primary ?? raw.isPrimary ?? false),
    sortOrder: Number(raw.sort_order ?? raw.sortOrder ?? 0),
  };
}

function normalizeStockStatus(raw: Record<string, unknown>): StockStatus {
  const status = String(raw.stock_status ?? raw.stockStatus ?? '').toUpperCase();
  if (status === 'LOW_STOCK') return 'LOW_STOCK';
  if (status === 'OUT_OF_STOCK') return 'OUT_OF_STOCK';
  const qty = Number(raw.stock_qty ?? raw.stockQuantity ?? 1);
  if (qty === 0) return 'OUT_OF_STOCK';
  if (qty <= 5) return 'LOW_STOCK';
  return 'IN_STOCK';
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function normalizeProduct(raw: Record<string, any>): Product {
  const mrp = Number(raw.price ?? raw.mrp ?? 0);
  const discountPct = Number(raw.discount_percentage ?? raw.discountPercent ?? 0);
  const price = Number(raw.discounted_price ?? (mrp * (1 - discountPct / 100)));
  const rawImages: Record<string, unknown>[] = Array.isArray(raw.images) ? raw.images : [];
  // List endpoint returns flat primary_image_url instead of images array
  if (rawImages.length === 0 && raw.primary_image_url) {
    rawImages.push({ cloudfront_url: raw.primary_image_url, is_primary: true, sort_order: 0, image_id: 'primary' });
  }

  return {
    id: String(raw.product_id ?? raw.id ?? ''),
    name: String(raw.name ?? ''),
    slug: String(raw.slug ?? ''),
    sku: String(raw.sku ?? ''),
    description: String(raw.description ?? ''),
    mrp,
    price,
    discountPercent: discountPct,
    stockStatus: normalizeStockStatus(raw),
    stockQuantity: Number(raw.stock_qty ?? raw.stockQuantity ?? 0),
    images: rawImages.map(normalizeImage),
    fabric: String(raw.fabric ?? raw.fabric_description ?? ''),
    color: String(raw.color ?? ''),
    weaveType: String(raw.work ?? raw.weave_type ?? raw.weaveType ?? ''),
    length: raw.saree_length != null ? Number(raw.saree_length) : (raw.length != null ? Number(raw.length) : undefined),
    blouseLength: raw.blouse_length != null ? Number(raw.blouse_length) : (raw.blouseLength != null ? Number(raw.blouseLength) : undefined),
    blouseIncluded: Boolean(raw.blouse_included ?? raw.blouseIncluded ?? false),
    careInstructions: String(raw.care_instructions ?? raw.careInstructions ?? ''),
    fabricCategories: [],
    occasionCategories: [],
    regionCategories: [],
    avgRating: Number(raw.average_rating ?? raw.avgRating ?? 0),
    reviewCount: Number(raw.review_count ?? raw.reviewCount ?? 0),
    isActive: Boolean(raw.is_active ?? raw.isActive ?? true),
    isFeatured: Boolean(raw.is_featured ?? raw.isFeatured ?? false),
    createdAt: String(raw.created_at ?? raw.createdAt ?? ''),
    updatedAt: String(raw.updated_at ?? raw.updatedAt ?? ''),
  };
}

function normalizeCategory(raw: Record<string, unknown>): Category {
  return {
    id: String(raw.category_id ?? raw.id ?? ''),
    name: String(raw.name ?? ''),
    slug: String(raw.slug ?? ''),
    type: (raw.type ?? 'FABRIC') as Category['type'],
    createdAt: String(raw.created_at ?? raw.createdAt ?? ''),
    updatedAt: String(raw.updated_at ?? raw.updatedAt ?? ''),
  };
}

// ─── API calls ────────────────────────────────────────────────────────────────

export const listProducts = async (filters: ProductFilters): Promise<PaginatedResponse<Product>> => {
  const params: Record<string, unknown> = {};
  if (filters.fabricIds?.length) params.fabric_ids = filters.fabricIds.join(',');
  if (filters.occasionIds?.length) params.occasion_ids = filters.occasionIds.join(',');
  if (filters.regionIds?.length) params.region_ids = filters.regionIds.join(',');
  if (filters.search) params.search = filters.search;
  if (filters.sort) params.sort = filters.sort.toUpperCase();
  if (filters.page) params.page = filters.page;
  if (filters.pageSize) params.page_size = filters.pageSize;

  const res = await apiClient.get('/products', { params });
  const raw = res.data;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const items: Product[] = (raw.items ?? raw.data ?? raw.products ?? []).map((p: any) => normalizeProduct(p));
  return {
    data: items,
    total: Number(raw.total_count ?? raw.total ?? items.length),
    page: Number(raw.page ?? 1),
    pageSize: Number(raw.page_size ?? raw.pageSize ?? 24),
    totalPages: Number(raw.total_pages ?? raw.totalPages ?? 1),
  };
};

export const getProductBySlug = async (slug: string): Promise<Product> => {
  const res = await apiClient.get(`/products/slug/${slug}`);
  return normalizeProduct(res.data.product ?? res.data);
};

export const getProductById = async (id: string): Promise<Product> => {
  const res = await apiClient.get(`/products/${id}`);
  return normalizeProduct(res.data.product ?? res.data);
};

export const getRelatedProducts = async (productId: string): Promise<Product[]> => {
  const res = await apiClient.get(`/products/${productId}/related`);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return (res.data.products ?? res.data ?? []).map((p: any) => normalizeProduct(p));
};

export const listCategories = async (type?: string): Promise<Category[]> => {
  const res = await apiClient.get('/categories', { params: type ? { type } : {} });
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return (res.data.categories ?? res.data ?? []).map((c: any) => normalizeCategory(c));
};

export const getPresignedUrl = async (productId: string, filename: string, contentType: string): Promise<{ presignedUrl: string; s3Key: string }> => {
  const res = await apiClient.post(
    `/products/${productId}/images/presigned-url`,
    null,
    { params: { filename, content_type: contentType } },
  );
  return { presignedUrl: res.data.presigned_url, s3Key: res.data.s3_key };
};

export const confirmImageUpload = async (productId: string, s3Key: string, isPrimary: boolean, sortOrder = 0): Promise<void> => {
  await apiClient.post(`/products/${productId}/images/confirm`, { s3_key: s3Key, is_primary: isPrimary, sort_order: sortOrder });
};

/**
 * Backend stores `price` (= MRP) + `discount_percentage`, and derives
 * discounted (selling) price = price * (1 - discount/100).
 * The admin form captures MRP and Selling Price, so we convert the pair
 * into the discount percentage the backend expects.
 */
function calcDiscountPct(mrp: number, sellingPrice: number): number {
  if (!mrp || mrp <= 0) return 0;
  if (!sellingPrice || sellingPrice >= mrp) return 0; // no discount (or invalid)
  const pct = ((mrp - sellingPrice) / mrp) * 100;
  return Math.round(pct * 100) / 100; // 2-decimal precision
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function toProductPayload(data: Partial<Product> & Record<string, any>) {
  const mrp = Number(data.mrp ?? data.price ?? 0);
  const sellingPrice = Number(data.price ?? data.mrp ?? 0);
  return {
    name: data.name,
    sku: data.sku,
    description: data.description ?? '',
    price: mrp,
    discount_percentage: calcDiscountPct(mrp, sellingPrice),
    stock_qty: data.stockQuantity ?? 0,
    is_active: data.isActive ?? true,
    fabric: data.fabric || null,
    color: data.color || null,
    work: data.weaveType || null,
    saree_length: data.length ? Number(data.length) : null,
    blouse_length: data.blouseLength ? Number(data.blouseLength) : null,
    blouse_included: Boolean(data.blouseIncluded),
    category_ids: [
      ...(data.fabricCategoryIds ?? []),
      ...(data.occasionCategoryIds ?? []),
      ...(data.regionCategoryIds ?? []),
    ],
  };
}

export const createProduct = async (data: Partial<Product>): Promise<Product> => {
  const res = await apiClient.post('/products', toProductPayload(data));
  return normalizeProduct(res.data.product ?? res.data);
};

export const updateProduct = async (id: string, data: Partial<Product>): Promise<Product> => {
  const payload: Record<string, unknown> = {};
  if (data.name !== undefined) payload.name = data.name;
  if (data.description !== undefined) payload.description = data.description;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const d = data as any;
  // MRP -> backend price; Selling Price -> derived discount_percentage
  if (d.mrp !== undefined || d.price !== undefined) {
    const mrp = Number(d.mrp ?? d.price ?? 0);
    const sellingPrice = Number(d.price ?? d.mrp ?? 0);
    payload.price = mrp;
    payload.discount_percentage = calcDiscountPct(mrp, sellingPrice);
  }
  if (d.stockQuantity !== undefined) payload.stock_qty = d.stockQuantity;
  if (data.isActive !== undefined) payload.is_active = data.isActive;
  // Attributes (form uses weaveType for Work, length for saree length)
  if (d.fabric !== undefined) payload.fabric = d.fabric || null;
  if (d.color !== undefined) payload.color = d.color || null;
  if (d.weaveType !== undefined) payload.work = d.weaveType || null;
  if (d.length !== undefined) payload.saree_length = d.length ? Number(d.length) : null;
  if (d.blouseLength !== undefined) payload.blouse_length = d.blouseLength ? Number(d.blouseLength) : null;
  if (d.blouseIncluded !== undefined) payload.blouse_included = Boolean(d.blouseIncluded);
  const catIds = [
    ...(d.fabricCategoryIds ?? []),
    ...(d.occasionCategoryIds ?? []),
    ...(d.regionCategoryIds ?? []),
  ];
  if (catIds.length > 0) payload.category_ids = catIds;
  const res = await apiClient.patch(`/products/${id}`, payload);
  return normalizeProduct(res.data.product ?? res.data);
};

export const deleteProduct = async (id: string): Promise<void> => {
  await apiClient.delete(`/products/${id}`);
};

export const bulkImport = async (file: File): Promise<{ imported: number; failed: number; errors: string[] }> => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await apiClient.post('/admin/products/bulk-import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};
