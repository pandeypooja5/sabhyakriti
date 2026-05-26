import { useCallback } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/store';
import { toggleWishlist } from '@/store/slices/wishlistSlice';

export const useWishlist = () => {
  const dispatch = useAppDispatch();
  const productIds = useAppSelector((s) => s.wishlist.productIds);

  const isWishlisted = useCallback(
    (productId: string) => productIds.includes(productId),
    [productIds]
  );

  const toggle = useCallback(
    (productId: string) => dispatch(toggleWishlist(productId)),
    [dispatch]
  );

  return { isWishlisted, toggle, productIds };
};
