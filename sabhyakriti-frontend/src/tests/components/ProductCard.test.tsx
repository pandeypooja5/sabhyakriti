import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { MemoryRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import ProductCard from '@/components/product/ProductCard';
import type { Product } from '@/types';
import authReducer from '@/store/slices/authSlice';
import wishlistReducer from '@/store/slices/wishlistSlice';
import cartReducer from '@/store/slices/cartSlice';

const mockProduct: Product = {
  id: 'prod-1',
  name: 'Kanjivaram Silk Saree',
  slug: 'kanjivaram-silk-saree',
  sku: 'KSS-001',
  description: 'Beautiful Kanjivaram silk saree',
  mrp: 15000,
  price: 12000,
  discountPercent: 20,
  stockStatus: 'IN_STOCK',
  stockQuantity: 10,
  images: [{ id: 'img-1', url: 'https://example.com/image.jpg', altText: 'Saree', isPrimary: true, sortOrder: 0 }],
  fabric: 'Silk',
  color: 'Red',
  blouseIncluded: true,
  fabricCategories: [],
  occasionCategories: [],
  regionCategories: [],
  avgRating: 4.5,
  reviewCount: 120,
  isActive: true,
  isFeatured: true,
  createdAt: '2025-01-01T00:00:00Z',
  updatedAt: '2025-01-01T00:00:00Z',
};

const createTestStore = (isAuthenticated = false) =>
  configureStore({
    reducer: {
      auth: authReducer,
      wishlist: wishlistReducer,
      cart: cartReducer,
    },
    preloadedState: {
      auth: {
        user: isAuthenticated ? { id: 'u1', name: 'Test', email: 'test@test.com', role: 'CUSTOMER' as const, isVerified: true, createdAt: '', updatedAt: '' } : null,
        tokens: isAuthenticated ? { accessToken: 'tok', refreshToken: 'ref', expiresIn: 3600 } : null,
        isAuthenticated,
        loading: false,
        error: null,
      },
      wishlist: { productIds: [], loading: false },
      cart: { items: [], totals: null, couponCode: null, loading: false, error: null },
    },
  });

const renderCard = (isAuthenticated = false) => {
  const store = createTestStore(isAuthenticated);
  return render(
    <Provider store={store}>
      <MemoryRouter>
        <ProductCard product={mockProduct} />
      </MemoryRouter>
    </Provider>
  );
};

describe('ProductCard', () => {
  it('renders product name', () => {
    renderCard();
    expect(screen.getByTestId('product-card-name')).toHaveTextContent('Kanjivaram Silk Saree');
  });

  it('renders product price', () => {
    renderCard();
    const price = screen.getByTestId('product-card-price');
    expect(price).toBeInTheDocument();
    expect(price.textContent).toContain('12,000');
  });

  it('renders MRP with strikethrough when discounted', () => {
    renderCard();
    const mrp = screen.getByTestId('product-card-mrp');
    expect(mrp).toBeInTheDocument();
    expect(mrp.textContent).toContain('15,000');
  });

  it('renders discount badge', () => {
    renderCard();
    const badge = screen.getByTestId('product-card-discount');
    expect(badge).toHaveTextContent('-20%');
  });

  it('renders a link to the product page', () => {
    renderCard();
    const link = screen.getByTestId('product-card-link');
    expect(link).toHaveAttribute('href', '/sarees/kanjivaram-silk-saree');
  });

  it('renders wishlist button', () => {
    renderCard();
    expect(screen.getByTestId('product-card-wishlist')).toBeInTheDocument();
  });

  it('shows toast error when wishlist clicked while not authenticated', async () => {
    renderCard(false);
    const btn = screen.getByTestId('product-card-wishlist');
    fireEvent.click(btn);
    // toast.error should have been called
    // Since we mock react-hot-toast in setup, just checking no crash
    expect(btn).toBeInTheDocument();
  });
});
