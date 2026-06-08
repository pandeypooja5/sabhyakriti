import apiClient from './apiClient';
import type { User, AuthTokens } from '@/types';

interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}

// In dev mode the backend auto-verifies and returns tokens immediately;
// in production it returns a message asking to verify email.
export const register = async (data: {
  full_name: string;
  email: string;
  password: string;
}): Promise<AuthResponse | { message: string }> => {
  const res = await apiClient.post('/auth/register', data);
  // If response has tokens, normalise and return as AuthResponse
  if (res.data?.tokens || res.data?.user) {
    return normalizeAuthResponse(res.data);
  }
  return res.data as { message: string };
};

// Normalize API response: snake_case → camelCase tokens + user fields
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function normalizeAuthResponse(raw: Record<string, any>): AuthResponse {
  const rawTokens = raw.tokens ?? raw;
  const tokens: AuthTokens = {
    accessToken: rawTokens.access_token ?? rawTokens.accessToken ?? '',
    refreshToken: rawTokens.refresh_token ?? rawTokens.refreshToken ?? '',
    expiresIn: rawTokens.expires_in ?? rawTokens.expiresIn ?? 1800,
  };
  const rawUser = raw.user ?? raw;
  const user: User = {
    id: String(rawUser.user_id ?? rawUser.id ?? ''),
    email: String(rawUser.email ?? ''),
    name: String(rawUser.full_name ?? rawUser.name ?? ''),
    role: (rawUser.role ?? 'CUSTOMER') as User['role'],
    isVerified: Boolean(rawUser.is_email_verified ?? rawUser.isVerified ?? false),
    createdAt: String(rawUser.created_at ?? rawUser.createdAt ?? ''),
    updatedAt: String(rawUser.updated_at ?? rawUser.updatedAt ?? ''),
  };
  return { user, tokens };
}

export const login = async (email: string, password: string): Promise<AuthResponse> => {
  const res = await apiClient.post('/auth/login', { email, password });
  return normalizeAuthResponse(res.data);
};

export const oauthLogin = async (provider: string, code: string): Promise<AuthResponse> => {
  const res = await apiClient.post('/auth/oauth/callback', { provider, code });
  return res.data;
};

export const sendOTP = async (phone: string): Promise<{ message: string }> => {
  // Backend expects snake_case `phone_number`
  const res = await apiClient.post('/auth/otp/send', { phone_number: phone });
  return res.data;
};

export const verifyOTP = async (phone: string, otp: string): Promise<AuthResponse> => {
  // Backend expects snake_case `phone_number` / `otp_code` and returns snake_case tokens
  const res = await apiClient.post('/auth/otp/verify', { phone_number: phone, otp_code: otp });
  return normalizeAuthResponse(res.data);
};

export const refresh = async (refreshToken: string): Promise<AuthResponse> => {
  const res = await apiClient.post('/auth/refresh', { refreshToken });
  return res.data;
};

export const logout = async (refreshToken: string): Promise<void> => {
  await apiClient.post('/auth/logout', { refreshToken });
};

export const forgotPassword = async (email: string): Promise<{ message: string }> => {
  const res = await apiClient.post('/auth/forgot-password', { email });
  return res.data;
};

export const resetPassword = async (token: string, password: string): Promise<{ message: string }> => {
  const res = await apiClient.post('/auth/reset-password', { token, password });
  return res.data;
};

export const changePassword = async (currentPassword: string, newPassword: string): Promise<{ message: string }> => {
  const res = await apiClient.post('/auth/change-password', { currentPassword, newPassword });
  return res.data;
};

export const getProfile = async (): Promise<User> => {
  const res = await apiClient.get('/auth/profile');
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const raw = (res.data.user ?? res.data) as Record<string, any>;
  return {
    id: String(raw.user_id ?? raw.id ?? ''),
    email: String(raw.email ?? ''),
    name: String(raw.full_name ?? raw.name ?? ''),
    phone: raw.phone_number ?? raw.phone ?? undefined,
    role: (raw.role ?? 'CUSTOMER') as User['role'],
    isVerified: Boolean(raw.is_email_verified ?? raw.isVerified ?? false),
    createdAt: String(raw.created_at ?? raw.createdAt ?? ''),
    updatedAt: String(raw.updated_at ?? raw.updatedAt ?? ''),
  };
};

export const updateProfile = async (data: Partial<Pick<User, 'name' | 'phone' | 'avatar'>>): Promise<User> => {
  const res = await apiClient.patch('/auth/profile', data);
  return res.data.user ?? res.data;
};

export const verifyEmail = async (token: string): Promise<{ message: string }> => {
  const res = await apiClient.get(`/auth/verify-email?token=${token}`);
  return res.data;
};
