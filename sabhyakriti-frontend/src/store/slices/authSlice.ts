import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import type { User, AuthTokens } from '@/types';
import * as authService from '@/services/authService';

interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

const storedTokens = (): AuthTokens | null => {
  try {
    const raw = localStorage.getItem('auth_tokens');
    return raw ? (JSON.parse(raw) as AuthTokens) : null;
  } catch {
    return null;
  }
};

const storedUser = (): User | null => {
  try {
    const raw = localStorage.getItem('auth_user');
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
};

const initialState: AuthState = {
  user: storedUser(),
  tokens: storedTokens(),
  isAuthenticated: !!storedTokens(),
  loading: false,
  error: null,
};

// ─── Thunks ────────────────────────────────────────────────────────────────────

export const loginWithEmail = createAsyncThunk(
  'auth/loginWithEmail',
  async (payload: { email: string; password: string }, { rejectWithValue }) => {
    try {
      const response = await authService.login(payload.email, payload.password);
      return response;
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      return rejectWithValue(error.response?.data?.message ?? 'Login failed');
    }
  }
);

export const loginWithOAuth = createAsyncThunk(
  'auth/loginWithOAuth',
  async (payload: { provider: string; code: string }, { rejectWithValue }) => {
    try {
      const response = await authService.oauthLogin(payload.provider, payload.code);
      return response;
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      return rejectWithValue(error.response?.data?.message ?? 'OAuth login failed');
    }
  }
);

export const loginWithOTP = createAsyncThunk(
  'auth/loginWithOTP',
  async (payload: { phone: string; otp: string }, { rejectWithValue }) => {
    try {
      const response = await authService.verifyOTP(payload.phone, payload.otp);
      return response;
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      return rejectWithValue(error.response?.data?.message ?? 'OTP verification failed');
    }
  }
);

export const refreshToken = createAsyncThunk(
  'auth/refreshToken',
  async (_, { getState, rejectWithValue }) => {
    const state = getState() as { auth: AuthState };
    const rt = state.auth.tokens?.refreshToken;
    if (!rt) return rejectWithValue('No refresh token');
    try {
      const response = await authService.refresh(rt);
      return response;
    } catch (err: unknown) {
      const error = err as { response?: { data?: { message?: string } } };
      return rejectWithValue(error.response?.data?.message ?? 'Token refresh failed');
    }
  }
);

export const logoutThunk = createAsyncThunk('auth/logout', async (_, { getState }) => {
  const state = getState() as { auth: AuthState };
  if (state.auth.tokens?.refreshToken) {
    try {
      await authService.logout(state.auth.tokens.refreshToken);
    } catch {
      // best-effort
    }
  }
});

// ─── Slice ─────────────────────────────────────────────────────────────────────

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials(state, action: PayloadAction<{ user: User; tokens: AuthTokens }>) {
      state.user = action.payload.user;
      state.tokens = action.payload.tokens;
      state.isAuthenticated = true;
      localStorage.setItem('auth_tokens', JSON.stringify(action.payload.tokens));
      localStorage.setItem('auth_user', JSON.stringify(action.payload.user));
    },
    clearAuth(state) {
      state.user = null;
      state.tokens = null;
      state.isAuthenticated = false;
      localStorage.removeItem('auth_tokens');
      localStorage.removeItem('auth_user');
    },
    updateUser(state, action: PayloadAction<User>) {
      state.user = action.payload;
      localStorage.setItem('auth_user', JSON.stringify(action.payload));
    },
  },
  extraReducers: (builder) => {
    const setLoading = (state: AuthState) => { state.loading = true; state.error = null; };
    const setError = (state: AuthState, action: PayloadAction<unknown>) => {
      state.loading = false;
      state.error = typeof action.payload === 'string' ? action.payload : 'An error occurred';
    };
    const setSuccess = (state: AuthState, action: PayloadAction<{ user: User; tokens: AuthTokens }>) => {
      state.loading = false;
      state.user = action.payload.user;
      state.tokens = action.payload.tokens;
      state.isAuthenticated = true;
      localStorage.setItem('auth_tokens', JSON.stringify(action.payload.tokens));
      localStorage.setItem('auth_user', JSON.stringify(action.payload.user));
    };

    builder
      .addCase(loginWithEmail.pending, setLoading)
      .addCase(loginWithEmail.fulfilled, setSuccess)
      .addCase(loginWithEmail.rejected, setError)
      .addCase(loginWithOAuth.pending, setLoading)
      .addCase(loginWithOAuth.fulfilled, setSuccess)
      .addCase(loginWithOAuth.rejected, setError)
      .addCase(loginWithOTP.pending, setLoading)
      .addCase(loginWithOTP.fulfilled, setSuccess)
      .addCase(loginWithOTP.rejected, setError)
      .addCase(refreshToken.fulfilled, (state, action: PayloadAction<{ user: User; tokens: AuthTokens }>) => {
        state.tokens = action.payload.tokens;
        localStorage.setItem('auth_tokens', JSON.stringify(action.payload.tokens));
      })
      .addCase(logoutThunk.fulfilled, (state) => {
        state.user = null;
        state.tokens = null;
        state.isAuthenticated = false;
        localStorage.removeItem('auth_tokens');
        localStorage.removeItem('auth_user');
      });
  },
});

export const { setCredentials, clearAuth, updateUser } = authSlice.actions;
export default authSlice.reducer;
