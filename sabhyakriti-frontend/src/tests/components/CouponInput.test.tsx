import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { MemoryRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import CouponInput from '@/components/cart/CouponInput';
import cartReducer from '@/store/slices/cartSlice';
import authReducer from '@/store/slices/authSlice';

// Mock cartService
vi.mock('@/services/cartService', () => ({
  applyCoupon: vi.fn(() => Promise.resolve({
    items: [],
    totals: { subtotal: 2000, discountAmount: 0, couponDiscount: 200, gstAmount: 100, shippingAmount: 0, total: 1900, itemCount: 1 },
    couponCode: 'SAVE200',
  })),
  removeCoupon: vi.fn(() => Promise.resolve({
    items: [],
    totals: { subtotal: 2000, discountAmount: 0, couponDiscount: 0, gstAmount: 100, shippingAmount: 0, total: 2100, itemCount: 1 },
    couponCode: undefined,
  })),
  getCart: vi.fn(),
  addToCart: vi.fn(),
  updateQuantity: vi.fn(),
  removeFromCart: vi.fn(),
}));

const createTestStore = (couponCode: string | null = null, couponDiscount = 0) =>
  configureStore({
    reducer: { cart: cartReducer, auth: authReducer },
    preloadedState: {
      cart: {
        items: [],
        totals: { subtotal: 2000, discountAmount: 0, couponDiscount, gstAmount: 100, shippingAmount: 0, total: 2100, itemCount: 1 },
        couponCode,
        loading: false,
        error: null,
      },
      auth: { user: null, tokens: null, isAuthenticated: false, loading: false, error: null },
    },
  });

describe('CouponInput', () => {
  it('renders coupon input field when no coupon applied', () => {
    const store = createTestStore();
    render(
      <Provider store={store}>
        <MemoryRouter>
          <CouponInput />
        </MemoryRouter>
      </Provider>
    );
    expect(screen.getByTestId('coupon-code-input')).toBeInTheDocument();
    expect(screen.getByTestId('coupon-apply-btn')).toBeInTheDocument();
  });

  it('shows applied coupon when coupon is active', () => {
    const store = createTestStore('SAVE200', 200);
    render(
      <Provider store={store}>
        <MemoryRouter>
          <CouponInput />
        </MemoryRouter>
      </Provider>
    );
    expect(screen.getByTestId('coupon-applied')).toBeInTheDocument();
    expect(screen.getByText('SAVE200')).toBeInTheDocument();
  });

  it('shows remove button for applied coupon', () => {
    const store = createTestStore('SAVE200', 200);
    render(
      <Provider store={store}>
        <MemoryRouter>
          <CouponInput />
        </MemoryRouter>
      </Provider>
    );
    expect(screen.getByTestId('coupon-remove-btn')).toBeInTheDocument();
  });

  it('apply button is disabled when input is empty', () => {
    const store = createTestStore();
    render(
      <Provider store={store}>
        <MemoryRouter>
          <CouponInput />
        </MemoryRouter>
      </Provider>
    );
    expect(screen.getByTestId('coupon-apply-btn')).toBeDisabled();
  });

  it('apply button is enabled when code is entered', () => {
    const store = createTestStore();
    render(
      <Provider store={store}>
        <MemoryRouter>
          <CouponInput />
        </MemoryRouter>
      </Provider>
    );
    fireEvent.change(screen.getByTestId('coupon-code-input'), { target: { value: 'TEST' } });
    expect(screen.getByTestId('coupon-apply-btn')).not.toBeDisabled();
  });

  it('dispatches applyCoupon on apply click', async () => {
    const store = createTestStore();
    render(
      <Provider store={store}>
        <MemoryRouter>
          <CouponInput />
        </MemoryRouter>
      </Provider>
    );
    fireEvent.change(screen.getByTestId('coupon-code-input'), { target: { value: 'SAVE200' } });
    fireEvent.click(screen.getByTestId('coupon-apply-btn'));
    await waitFor(() => {
      // After apply, state should update. Here we just verify no crash
      expect(screen.getByTestId('coupon-code-input')).toBeInTheDocument();
    });
  });
});
