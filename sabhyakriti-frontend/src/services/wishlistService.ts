import apiClient from './apiClient';
import type { WishlistItem, Product } from '@/types';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function normalizeWishlistItem(raw: any): WishlistItem {
  const img = raw.primary_image_url ?? raw.primaryImageUrl ?? '';
  return {
    id: String(raw.wishlist_item_id ?? raw.id ?? ''),
    productId: String(raw.product_id ?? raw.productId ?? ''),
    addedAt: String(raw.created_at ?? raw.addedAt ?? ''),
    product: {
      id: String(raw.product_id ?? ''),
      name: String(raw.product_name ?? raw.name ?? ''),
      slug: String(raw.slug ?? raw.product_slug ?? ''),
      sku: '',
      description: '',
      price: Number(raw.discounted_price ?? 0),
      mrp: Number(raw.price ?? raw.discounted_price ?? 0),
      discountPercent: 0,
      stockStatus: (raw.stock_status ?? 'IN_STOCK'),
      stockQuantity: 0,
      images: img ? [{ url: img, isPrimary: true, altText: '', id: '', sortOrder: 0 }] : [],
      fabric: '',
      blouseIncluded: false,
      careInstructions: '',
      fabricCategories: [],
      occasionCategories: [],
      regionCategories: [],
      avgRating: 0,
      reviewCount: 0,
      isActive: true,
      isFeatured: false,
      createdAt: '',
      updatedAt: '',
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } as any as Product,
  };
}

export const getWishlist = async (): Promise<WishlistItem[]> => {
  const res = await apiClient.get('/wishlist');
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const items = (res.data.items ?? res.data ?? []) as any[];
  return items.map(normalizeWishlistItem);
};

export const addToWishlist = async (productId: string): Promise<WishlistItem[]> => {
  const res = await apiClient.post('/wishlist/items', { product_id: productId });
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const items = (res.data.items ?? []) as any[];
  return items.map(normalizeWishlistItem);
};

export const removeFromWishlist = async (productId: string): Promise<void> => {
  await apiClient.delete(`/wishlist/items/${productId}`);
};
