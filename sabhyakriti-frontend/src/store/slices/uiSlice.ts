import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface ModalState {
  cancelOrder: { open: boolean; orderId: string | null };
  returnRequest: { open: boolean; orderId: string | null };
  sizeGuide: { open: boolean };
  lightbox: { open: boolean; images: string[]; currentIndex: number };
}

interface UIState {
  modals: ModalState;
  miniCartOpen: boolean;
  mobileMenuOpen: boolean;
}

const initialState: UIState = {
  modals: {
    cancelOrder: { open: false, orderId: null },
    returnRequest: { open: false, orderId: null },
    sizeGuide: { open: false },
    lightbox: { open: false, images: [], currentIndex: 0 },
  },
  miniCartOpen: false,
  mobileMenuOpen: false,
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    openCancelOrderModal(state, action: PayloadAction<string>) {
      state.modals.cancelOrder = { open: true, orderId: action.payload };
    },
    closeCancelOrderModal(state) {
      state.modals.cancelOrder = { open: false, orderId: null };
    },
    openReturnModal(state, action: PayloadAction<string>) {
      state.modals.returnRequest = { open: true, orderId: action.payload };
    },
    closeReturnModal(state) {
      state.modals.returnRequest = { open: false, orderId: null };
    },
    openSizeGuide(state) {
      state.modals.sizeGuide.open = true;
    },
    closeSizeGuide(state) {
      state.modals.sizeGuide.open = false;
    },
    openLightbox(state, action: PayloadAction<{ images: string[]; index: number }>) {
      state.modals.lightbox = { open: true, images: action.payload.images, currentIndex: action.payload.index };
    },
    closeLightbox(state) {
      state.modals.lightbox = { open: false, images: [], currentIndex: 0 };
    },
    setLightboxIndex(state, action: PayloadAction<number>) {
      state.modals.lightbox.currentIndex = action.payload;
    },
    toggleMiniCart(state) {
      state.miniCartOpen = !state.miniCartOpen;
    },
    setMiniCartOpen(state, action: PayloadAction<boolean>) {
      state.miniCartOpen = action.payload;
    },
    toggleMobileMenu(state) {
      state.mobileMenuOpen = !state.mobileMenuOpen;
    },
    setMobileMenuOpen(state, action: PayloadAction<boolean>) {
      state.mobileMenuOpen = action.payload;
    },
  },
});

export const {
  openCancelOrderModal,
  closeCancelOrderModal,
  openReturnModal,
  closeReturnModal,
  openSizeGuide,
  closeSizeGuide,
  openLightbox,
  closeLightbox,
  setLightboxIndex,
  toggleMiniCart,
  setMiniCartOpen,
  toggleMobileMenu,
  setMobileMenuOpen,
} = uiSlice.actions;
export default uiSlice.reducer;
