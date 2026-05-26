import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { Order } from '@/types';
import * as orderService from '@/services/orderService';

interface OrderState {
  orders: Order[];
  currentOrder: Order | null;
  total: number;
  page: number;
  loading: boolean;
  error: string | null;
}

const initialState: OrderState = {
  orders: [],
  currentOrder: null,
  total: 0,
  page: 1,
  loading: false,
  error: null,
};

export const fetchOrders = createAsyncThunk(
  'orders/fetchOrders',
  async (params: { page?: number; pageSize?: number } = {}, { rejectWithValue }) => {
    try {
      return await orderService.listOrders(params.page ?? 1, params.pageSize ?? 10);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      return rejectWithValue(error.response?.data?.message ?? 'Failed to fetch orders');
    }
  }
);

export const fetchOrderDetail = createAsyncThunk(
  'orders/fetchOrderDetail',
  async (orderId: string, { rejectWithValue }) => {
    try {
      return await orderService.getOrderDetail(orderId);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      return rejectWithValue(error.response?.data?.message ?? 'Failed to fetch order');
    }
  }
);

export const cancelOrder = createAsyncThunk(
  'orders/cancelOrder',
  async (payload: { orderId: string; reason: string }, { rejectWithValue }) => {
    try {
      return await orderService.cancelOrder(payload.orderId, payload.reason);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      return rejectWithValue(error.response?.data?.message ?? 'Failed to cancel order');
    }
  }
);

const orderSlice = createSlice({
  name: 'orders',
  initialState,
  reducers: {
    setCurrentOrder(state, action) {
      state.currentOrder = action.payload;
    },
    clearCurrentOrder(state) {
      state.currentOrder = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchOrders.pending, (state) => { state.loading = true; })
      .addCase(fetchOrders.fulfilled, (state, action) => {
        state.loading = false;
        state.orders = action.payload.data;
        state.total = action.payload.total;
        state.page = action.payload.page;
      })
      .addCase(fetchOrders.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      .addCase(fetchOrderDetail.pending, (state) => { state.loading = true; })
      .addCase(fetchOrderDetail.fulfilled, (state, action) => {
        state.loading = false;
        state.currentOrder = action.payload;
      })
      .addCase(fetchOrderDetail.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      .addCase(cancelOrder.fulfilled, (state, action) => {
        const idx = state.orders.findIndex((o) => o.id === action.payload.id);
        if (idx >= 0) state.orders[idx] = action.payload;
        if (state.currentOrder?.id === action.payload.id) state.currentOrder = action.payload;
      });
  },
});

export const { setCurrentOrder, clearCurrentOrder } = orderSlice.actions;
export default orderSlice.reducer;
