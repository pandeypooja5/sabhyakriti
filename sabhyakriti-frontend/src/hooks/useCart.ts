import { useCallback } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/store';
import {
  fetchCart,
  addToCart as addToCartThunk,
  updateQuantity as updateQuantityThunk,
  removeFromCart as removeFromCartThunk,
  applyCoupon as applyCouponThunk,
  removeCoupon as removeCouponThunk,
} from '@/store/slices/cartSlice';

export const useCart = () => {
  const dispatch = useAppDispatch();
  const cart = useAppSelector((s) => s.cart);

  const itemCount = cart.items.reduce((acc, item) => acc + item.quantity, 0);

  const refetchCart = useCallback(() => dispatch(fetchCart()), [dispatch]);

  const addItem = useCallback(
    (productId: string, quantity = 1) => dispatch(addToCartThunk({ productId, quantity })),
    [dispatch]
  );

  const updateItem = useCallback(
    (itemId: string, quantity: number) => dispatch(updateQuantityThunk({ itemId, quantity })),
    [dispatch]
  );

  const removeItem = useCallback(
    (itemId: string) => dispatch(removeFromCartThunk(itemId)),
    [dispatch]
  );

  const applyCode = useCallback(
    (code: string) => dispatch(applyCouponThunk(code)),
    [dispatch]
  );

  const removeCode = useCallback(() => dispatch(removeCouponThunk()), [dispatch]);

  return {
    ...cart,
    itemCount,
    refetchCart,
    addItem,
    updateItem,
    removeItem,
    applyCode,
    removeCode,
  };
};
