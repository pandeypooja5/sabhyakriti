import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import type { CartItem, CartTotals } from '@/types';
import * as cartService from '@/services/cartService';

interface CartState {
  items: CartItem[];
  totals: CartTotals | null;
  couponCode: string | null;
  loading: boolean;
  error: string | null;
}

const initialState: CartState = {
  items: [],
  totals: null,
  couponCode: null,
  loading: false,
  error: null,
};

export const fetchCart = createAsyncThunk('cart/fetchCart', async (_, { rejectWithValue }) => {
  try {
    return await cartService.getCart();
  } catch (err: unknown) {
    const error = err as { response?: { data?: { message?: string } } };
    return rejectWithValue(error.response?.data?.message ?? 'Failed to fetch cart');
  }
});

export const addToCart = createAsyncThunk(
  'cart/addToCart',
  async (payload: { productId: string; quantity: number }, { rejectWithValue }) => {
    try {
      return await cartService.addToCart(payload.productId, payload.quantity);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      return rejectWithValue(error.response?.data?.message ?? 'Failed to add to cart');
    }
  }
);

export const updateQuantity = createAsyncThunk(
  'cart/updateQuantity',
  async (payload: { itemId: string; quantity: number }, { rejectWithValue }) => {
    try {
      return await cartService.updateQuantity(payload.itemId, payload.quantity);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      return rejectWithValue(error.response?.data?.message ?? 'Failed to update quantity');
    }
  }
);

export const removeFromCart = createAsyncThunk(
  'cart/removeFromCart',
  async (itemId: string, { rejectWithValue }) => {
    try {
      await cartService.removeFromCart(itemId);
      return itemId;
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      return rejectWithValue(error.response?.data?.message ?? 'Failed to remove from cart');
    }
  }
);

export const applyCoupon = createAsyncThunk(
  'cart/applyCoupon',
  async (code: string, { rejectWithValue }) => {
    try {
      return await cartService.applyCoupon(code);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      return rejectWithValue(error.response?.data?.message ?? 'Invalid coupon code');
    }
  }
);

export const removeCoupon = createAsyncThunk('cart/removeCoupon', async (_, { rejectWithValue }) => {
  try {
    return await cartService.removeCoupon();
  } catch (err: unknown) {
    const error = err as { response?: { data?: { message?: string } } };
    return rejectWithValue(error.response?.data?.message ?? 'Failed to remove coupon');
  }
});

interface CartResponse {
  items: CartItem[];
  totals: CartTotals;
  couponCode?: string;
}

const cartSlice = createSlice({
  name: 'cart',
  initialState,
  reducers: {
    clearCart(state) {
      state.items = [];
      state.totals = null;
      state.couponCode = null;
    },
  },
  extraReducers: (builder) => {
    const handleCartResponse = (state: CartState, action: PayloadAction<CartResponse>) => {
      state.loading = false;
      state.items = action.payload.items;
      state.totals = action.payload.totals;
      state.couponCode = action.payload.couponCode ?? null;
    };

    builder
      .addCase(fetchCart.pending, (state) => { state.loading = true; })
      .addCase(fetchCart.fulfilled, handleCartResponse)
      .addCase(fetchCart.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      .addCase(addToCart.pending, (state) => { state.loading = true; })
      .addCase(addToCart.fulfilled, handleCartResponse)
      .addCase(addToCart.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      .addCase(updateQuantity.fulfilled, handleCartResponse)
      .addCase(removeFromCart.fulfilled, (state, action) => {
        state.items = state.items.filter((i) => i.id !== action.payload);
      })
      .addCase(applyCoupon.fulfilled, handleCartResponse)
      .addCase(applyCoupon.rejected, (state, action) => {
        state.error = action.payload as string;
      })
      .addCase(removeCoupon.fulfilled, handleCartResponse);
  },
});

export const { clearCart } = cartSlice.actions;
export default cartSlice.reducer;
