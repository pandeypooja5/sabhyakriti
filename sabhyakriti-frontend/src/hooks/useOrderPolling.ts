import { useEffect, useRef } from 'react';
import { useAppDispatch } from '@/store/store';
import { fetchOrderDetail } from '@/store/slices/orderSlice';
import type { OrderStatus } from '@/types';

const ACTIVE_STATUSES: OrderStatus[] = ['PENDING', 'CONFIRMED', 'PROCESSING', 'SHIPPED', 'OUT_FOR_DELIVERY'];
const POLL_INTERVAL_MS = 30_000;

export const useOrderPolling = (orderId: string | null, currentStatus?: OrderStatus) => {
  const dispatch = useAppDispatch();
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!orderId) return;
    if (currentStatus && !ACTIVE_STATUSES.includes(currentStatus)) return;

    const poll = () => {
      dispatch(fetchOrderDetail(orderId));
    };

    intervalRef.current = setInterval(poll, POLL_INTERVAL_MS);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [dispatch, orderId, currentStatus]);

  // Stop polling when delivered or terminal state
  useEffect(() => {
    if (!currentStatus) return;
    if (!ACTIVE_STATUSES.includes(currentStatus) && intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, [currentStatus]);
};
