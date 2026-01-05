import { baseApi, AUTH_TOKEN_KEY } from './baseApi';

// Types for auth responses
export interface User {
  id: string;
  email: string;
  name: string;
  is_active: boolean;
  created_at?: string;
  last_login_at?: string;
}

export interface AuthData {
  user: User;
  token: string;
  expires_at: string;
}

export interface AuthResponse {
  success: boolean;
  data: AuthData;
}

export interface MeResponse {
  success: boolean;
  data: User;
}

export interface LogoutResponse {
  success: boolean;
  message: string;
}

// Request types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

// Auth API endpoints
export const authApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Login endpoint
    login: builder.mutation<AuthResponse, LoginRequest>({
      query: (credentials) => ({
        url: '/api/v1/auth/login',
        method: 'POST',
        body: credentials,
      }),
      // On successful login, store token in localStorage
      async onQueryStarted(_, { queryFulfilled }) {
        try {
          const { data } = await queryFulfilled;
          if (data.success && data.data.token) {
            localStorage.setItem(AUTH_TOKEN_KEY, data.data.token);
            localStorage.setItem('auth_user', JSON.stringify(data.data.user));
          }
        } catch {
          // Login failed - don't store anything
        }
      },
      invalidatesTags: ['Auth'],
    }),

    // Register endpoint
    register: builder.mutation<AuthResponse, RegisterRequest>({
      query: (userData) => ({
        url: '/api/v1/auth/register',
        method: 'POST',
        body: userData,
      }),
      // On successful registration, store token in localStorage
      async onQueryStarted(_, { queryFulfilled }) {
        try {
          const { data } = await queryFulfilled;
          if (data.success && data.data.token) {
            localStorage.setItem(AUTH_TOKEN_KEY, data.data.token);
            localStorage.setItem('auth_user', JSON.stringify(data.data.user));
          }
        } catch {
          // Registration failed - don't store anything
        }
      },
      invalidatesTags: ['Auth'],
    }),

    // Get current user endpoint
    getMe: builder.query<MeResponse, void>({
      query: () => '/api/v1/auth/me',
      providesTags: ['Auth'],
    }),

    // Logout endpoint
    logout: builder.mutation<LogoutResponse, void>({
      query: () => ({
        url: '/api/v1/auth/logout',
        method: 'POST',
      }),
      // On logout, clear localStorage
      async onQueryStarted(_, { queryFulfilled }) {
        try {
          await queryFulfilled;
        } finally {
          // Always clear local storage on logout attempt
          localStorage.removeItem(AUTH_TOKEN_KEY);
          localStorage.removeItem('auth_user');
        }
      },
      invalidatesTags: ['Auth'],
    }),

    // Logout from all devices
    logoutAll: builder.mutation<LogoutResponse, void>({
      query: () => ({
        url: '/api/v1/auth/logout-all',
        method: 'POST',
      }),
      async onQueryStarted(_, { queryFulfilled }) {
        try {
          await queryFulfilled;
        } finally {
          localStorage.removeItem(AUTH_TOKEN_KEY);
          localStorage.removeItem('auth_user');
        }
      },
      invalidatesTags: ['Auth'],
    }),
  }),
});

// Export hooks
export const {
  useLoginMutation,
  useRegisterMutation,
  useGetMeQuery,
  useLazyGetMeQuery,
  useLogoutMutation,
  useLogoutAllMutation,
} = authApi;

// Helper functions
export const getStoredToken = (): string | null => {
  return localStorage.getItem(AUTH_TOKEN_KEY);
};

export const getStoredUser = (): User | null => {
  const userStr = localStorage.getItem('auth_user');
  if (userStr) {
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }
  return null;
};

export const isAuthenticated = (): boolean => {
  return !!getStoredToken();
};

export const clearAuthData = (): void => {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem('auth_user');
};

