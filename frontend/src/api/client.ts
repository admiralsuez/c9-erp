import axios from 'axios';
import toast from 'react-hot-toast';
import type { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

// API base URL strategy:
// - Default: relative '/api' (same origin as the page - no mixed content, no CORS).
//   The reverse proxy (nginx / DO App Platform / Vite dev proxy) strips '/api'
//   and forwards to the backend.
// - Override: set VITE_API_URL at build time only if the API lives on another origin.
//   It must then be an https:// URL when the site is served over https.
export const API_BASE_URL: string = import.meta.env.VITE_API_URL || '/api';

// Create axios instance
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============ Single-flight token refresh ============
// When several requests fail with 401 in the same tick (e.g. page-load fan-out
// after the access token has just expired) we previously kicked off N parallel
// /auth/refresh calls. Only one would succeed with the new token; the others
// would clobber localStorage with stale tokens and the original requests would
// then fail again. ``pendingRefresh`` shares one promise across all in-flight
// 401s so only one refresh goes out, and all queued requests reuse its result.
let pendingRefresh: Promise<string> | null = null;

// Exported for unit tests (see src/test/api-client.test.ts) so the
// single-flight behaviour can be exercised without needing a full HTTP round
// trip through the response interceptor.
export async function refreshAccessToken(): Promise<string> {
  if (pendingRefresh) return pendingRefresh;

  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }

  pendingRefresh = axios
    .post(`${API_BASE_URL}/auth/refresh`, { refresh_token: refreshToken })
    .then((res) => {
      const newAccessToken = res.data.access_token;
      localStorage.setItem('access_token', newAccessToken);
      return newAccessToken;
    })
    .finally(() => {
      // Reset after the in-flight batch settles so a future 401 can refresh again.
      pendingRefresh = null;
    });

  return pendingRefresh;
}

// Test-only: reset the in-flight refresh promise so unit tests have a clean
// module state between cases. Not part of the public API surface.
export function __resetPendingRefreshForTests(): void {
  pendingRefresh = null;
}

function clearAuthAndRedirectToLogin(): void {
  // NOTE: This runs inside an axios response interceptor, outside of React's
  // render tree, so we cannot use react-router's ``useNavigate`` here.
  // ``window.location.href`` is intentional: when the *access token* refresh
  // fails for an arbitrary background request (e.g. a 401 from a non-route
  // page) we want a hard reload to reset the in-memory AuthContext state.
  // All navigations triggered from React components (logout button, etc.)
  // go through ``useNavigate`` instead — see AuthContext.tsx.
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  window.location.href = '/login';
}

// Request interceptor for JWT token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling 401 and token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      // Don't redirect if already on login page
      if (window.location.pathname === '/login') {
        return Promise.reject(error);
      }

      originalRequest._retry = true;

      try {
        const newAccessToken = await refreshAccessToken();
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed — wipe tokens and bounce to login.
        toast.error('Session expired. Please log in again.');
        clearAuthAndRedirectToLogin();
        return Promise.reject(refreshError);
      }
    }

    // Show toast for 5xx errors
    if (error.response?.status && error.response.status >= 500) {
      toast.error('Server error. Please try again later.');
    }

    // Show toast for network errors
    if (!error.response && error.message === 'Network Error') {
      toast.error('Network error. Check your connection.');
    }

    return Promise.reject(error);
  }
);

export default apiClient;
