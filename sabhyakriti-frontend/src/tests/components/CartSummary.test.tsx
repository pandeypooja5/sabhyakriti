import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import { MemoryRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import CartSummary from '@/components/cart/CartSummary';
import cartReducer from '@/store/slices/cartSlice';
import authReducer from '@/store/slices/authSlice';

const makeTotals = (subtotal: number, couponDiscount = 0) => {
  const gst = Math.round(subtotal * 0.05 * 100) / 100;
  return {
    subtotal,
    discountAmount: 0,
    couponDiscount,
    gstAmount: gst,
    shippingAmount: subtotal >= 999 ? 0 : 99,
    total: subtotal - couponDiscount + gst + (subtotal >= 999 ? 0 : 99),
    itemCount: 2,
  };
};

const createTestStore = (subtotal = 2000, couponCode: string | null = null, couponDiscount = 0) =>
  configureStore({
    reducer: { cart: cartReducer, auth: authReducer },
    preloadedState: {
      cart: {
        items: [],
        totals: makeTotals(subtotal, couponDiscount),
        couponCode,
        loading: false,
        error: null,
      },
      auth: { user: null, tokens: null, isAuthenticated: false, loading: false, error: null },
    },
  });

describe('CartSummary', () => {
  it('renders subtotal correctly', () => {
    const store = createTestStore(2000);
    render(
      <Provider store={store}>
        <MemoryRouter>
          <CartSummary />
        </MemoryRouter>
      </Provider>
    );
    const subtotal = screen.getByTestId('summary-subtotal');
    expect(subtotal.textContent).toContain('2,000');
  });

  it('displays GST as 5% of subtotal', () => {
    const store = createTestStore(2000);
    render(
      <Provider store={store}>
        <MemoryRouter>
          <CartSummary />
        </MemoryRouter>
      </Provider>
    );
    const gst = screen.getByTestId('summary-gst');
    // 5% of 2000 = 100
    expect(gst.textContent).toContain('100');
  });

  it('shows FREE shipping for orders above ₹999', () => {
    const store = createTestStore(2000);
    render(
      <Provider store={store}>
        <MemoryRouter>
          <CartSummary />
        </MemoryRouter>
      </Provider>
    );
    const shipping = screen.getByTestId('summary-shipping');
    expect(shipping.textContent).toBe('FREE');
  });

  it('shows shipping charge for orders below ₹999', () => {
    const store = createTestStore(500);
    render(
      <Provider store={store}>
        <MemoryRouter>
          <CartSummary />
        </MemoryRouter>
      </Provider>
    );
    const shipping = screen.getByTestId('summary-shipping');
    expect(shipping.textContent).toContain('99');
  });

  it('shows coupon discount when applied', () => {
    const store = createTestStore(2000, 'SAVE200', 200);
    render(
      <Provider store={store}>
        <MemoryRouter>
          <CartSummary />
        </MemoryRouter>
      </Provider>
    );
    const coupon = screen.getByTestId('summary-coupon');
    expect(coupon.textContent).toContain('200');
  });

  it('renders checkout button by default', () => {
    const store = createTestStore(2000);
    render(
      <Provider store={store}>
        <MemoryRouter>
          <CartSummary />
        </MemoryRouter>
      </Provider>
    );
    expect(screen.getByTestId('checkout-btn')).toBeInTheDocument();
  });

  it('hides checkout button when showCheckoutBtn=false', () => {
    const store = createTestStore(2000);
    render(
      <Provider store={store}>
        <MemoryRouter>
          <CartSummary showCheckoutBtn={false} />
        </MemoryRouter>
      </Provider>
    );
    expect(screen.queryByTestId('checkout-btn')).not.toBeInTheDocument();
  });
});
