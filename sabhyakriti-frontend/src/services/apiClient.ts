import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
import type { AuthTokens } from '@/types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ─── Request Interceptor: inject JWT ──────────────────────────────────────────

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const raw = localStorage.getItem('auth_tokens');
    if (raw) {
      try {
        const tokens: AuthTokens = JSON.parse(raw);
        config.headers.Authorization = `Bearer ${tokens.accessToken}`;
      } catch {
        // ignore parse errors
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ─── Response Interceptor: 401 → refresh ─────────────────────────────────────

let isRefreshing = false;
let failedQueue: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = [];

const processQueue = (error: unknown, token: string | null) => {
  failedQueue.forEach((prom) => {
    if (error) prom.reject(error);
    else if (token) prom.resolve(token);
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const raw = localStorage.getItem('auth_tokens');
        if (!raw) throw new Error('No refresh token');
        const { refreshToken } = JSON.parse(raw) as AuthTokens;

        const response = await axios.post(`${BASE_URL}/auth/refresh`, { refreshToken });
        const newTokens: AuthTokens = response.data.tokens ?? response.data;

        localStorage.setItem('auth_tokens', JSON.stringify(newTokens));
        apiClient.defaults.headers.common.Authorization = `Bearer ${newTokens.accessToken}`;
        originalRequest.headers.Authorization = `Bearer ${newTokens.accessToken}`;
        processQueue(null, newTokens.accessToken);
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        localStorage.removeItem('auth_tokens');
        localStorage.removeItem('auth_user');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
