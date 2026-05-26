import { useCallback } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/store';
import { loginWithEmail, logoutThunk } from '@/store/slices/authSlice';
import type { UserRole } from '@/types';

export const useAuth = () => {
  const dispatch = useAppDispatch();
  const { user, isAuthenticated, loading, error } = useAppSelector((s) => s.auth);

  const isAdmin: boolean = user?.role === ('ADMIN' as UserRole) || user?.role === ('SUPER_ADMIN' as UserRole);

  const login = useCallback(
    (email: string, password: string) => dispatch(loginWithEmail({ email, password })),
    [dispatch]
  );

  const logout = useCallback(() => dispatch(logoutThunk()), [dispatch]);

  return { user, isAuthenticated, isAdmin, loading, error, login, logout };
};
