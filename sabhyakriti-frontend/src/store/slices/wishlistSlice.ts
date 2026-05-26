import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import * as wishlistService from '@/services/wishlistService';

interface WishlistState {
  productIds: string[];
  loading: boolean;
}

const initialState: WishlistState = {
  productIds: [],
  loading: false,
};

export const fetchWishlist = createAsyncThunk('wishlist/fetch', async (_, { rejectWithValue }) => {
  try {
    const items = await wishlistService.getWishlist();
    return items.map((item) => item.productId);
  } catch (err: unknown) {
    const error = err as { response?: { data?: { message?: string } } };
    return rejectWithValue(error.response?.data?.message ?? 'Failed to fetch wishlist');
  }
});

export const toggleWishlist = createAsyncThunk(
  'wishlist/toggle',
  async (productId: string, { getState, rejectWithValue }) => {
    const state = getState() as { wishlist: WishlistState };
    const isWishlisted = state.wishlist.productIds.includes(productId);
    try {
      if (isWishlisted) {
        await wishlistService.removeFromWishlist(productId);
      } else {
        await wishlistService.addToWishlist(productId);
      }
      return { productId, wasWishlisted: isWishlisted };
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      return rejectWithValue(error.response?.data?.message ?? 'Wishlist update failed');
    }
  }
);

const wishlistSlice = createSlice({
  name: 'wishlist',
  initialState,
  reducers: {
    setWishlist(state, action: PayloadAction<string[]>) {
      state.productIds = action.payload;
    },
    clearWishlist(state) {
      state.productIds = [];
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchWishlist.pending, (state) => { state.loading = true; })
      .addCase(fetchWishlist.fulfilled, (state, action) => {
        state.loading = false;
        state.productIds = action.payload;
      })
      .addCase(fetchWishlist.rejected, (state) => { state.loading = false; })
      .addCase(toggleWishlist.fulfilled, (state, action) => {
        const { productId, wasWishlisted } = action.payload;
        if (wasWishlisted) {
          state.productIds = state.productIds.filter((id) => id !== productId);
        } else {
          state.productIds.push(productId);
        }
      });
  },
});

export const { setWishlist, clearWishlist } = wishlistSlice.actions;
export default wishlistSlice.reducer;
