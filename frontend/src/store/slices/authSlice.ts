/**
 * ==============================================
 * 认证 Redux Slice
 * ==============================================
 */

import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';

interface User {
  id: string;
  username: string;
  email?: string;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  accessToken: null,
  isAuthenticated: false,
  loading: false,
  error: null,
};

// 从 localStorage 加载 Token
const loadTokenFromStorage = (): string | null => {
  try {
    const authState = localStorage.getItem('auth');
    if (authState) {
      const auth = JSON.parse(authState);
      return auth.accessToken || null;
    }

    const token = localStorage.getItem('token');
    if (token) {
      return token;
    }

    return null;
  } catch (error) {
    console.error('❌ 加载 Token 失败:', error);
    return null;
  }
};

// 异步登录 Thunk
export const loginAsync = createAsyncThunk(
  'auth/login',
  async (credentials: { username: string; password: string }, { rejectWithValue }) => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return rejectWithValue(errorData.detail || '登录失败');
      }

      const data = await response.json();
      return data;
    } catch (error) {
      return rejectWithValue('网络错误，请检查后端是否运行');
    }
  }
);

// 异步登出 Thunk
export const logoutAsync = createAsyncThunk('auth/logout', async () => {
  // 可选：调用后端登出 API
  return;
});

const authSlice = createSlice({
  name: 'auth',
  initialState: {
    ...initialState,
    accessToken: loadTokenFromStorage(),
    isAuthenticated: !!loadTokenFromStorage(),
  },
  reducers: {
    setCredentials(state, action: PayloadAction<{ user: User; accessToken: string }>) {
      const { user, accessToken } = action.payload;
      state.user = user;
      state.accessToken = accessToken;
      state.isAuthenticated = true;

      // 保存到 localStorage
      localStorage.setItem(
        'auth',
        JSON.stringify({
          accessToken,
          user,
        })
      );
      localStorage.setItem('token', accessToken);
    },

    clearCredentials(state) {
      state.user = null;
      state.accessToken = null;
      state.isAuthenticated = false;

      // 清除 localStorage
      localStorage.removeItem('auth');
      localStorage.removeItem('token');
    },

    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // 登录中
      .addCase(loginAsync.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      // 登录成功
      .addCase(loginAsync.fulfilled, (state, action) => {
        state.loading = false;
        state.accessToken = action.payload.access_token;
        state.user = {
          id: action.payload.user_id?.toString() || '1',
          username: action.payload.username || 'Unknown',
        };
        state.isAuthenticated = true;

        // 保存到 localStorage
        localStorage.setItem(
          'auth',
          JSON.stringify({
            accessToken: action.payload.access_token,
            user: state.user,
          })
        );
        localStorage.setItem('token', action.payload.access_token);
      })
      // 登录失败
      .addCase(loginAsync.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // 登出
      .addCase(logoutAsync.fulfilled, (state) => {
        state.user = null;
        state.accessToken = null;
        state.isAuthenticated = false;

        // 清除 localStorage
        localStorage.removeItem('auth');
        localStorage.removeItem('token');
      });
  },
});

export const { setCredentials, clearCredentials, clearError } = authSlice.actions;
export const authActions = authSlice.actions;

export default authSlice.reducer;

// Selectors
export const selectUser = (state: { auth: AuthState }) => state.auth.user;
export const selectAccessToken = (state: { auth: AuthState }) => state.auth.accessToken;
export const selectIsAuthenticated = (state: { auth: AuthState }) => state.auth.isAuthenticated;
export const selectAuthLoading = (state: { auth: AuthState }) => state.auth.loading;
export const selectAuthError = (state: { auth: AuthState }) => state.auth.error;
