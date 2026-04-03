/**
 * API client with auth interceptors
 */
import axios from 'axios';

function resolveApiBaseUrl() {
  const raw = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (!raw) return 'http://localhost:8001/api/v1';
  return raw.endsWith('/api/v1')
    ? raw
    : `${raw.replace(/\/+$/, '')}/api/v1`;
}

export const api = axios.create({
  baseURL: resolveApiBaseUrl(),
  headers: { 'Content-Type': 'application/json' },
});

export const authInterceptor = {
  setToken(_token: string | null) {
    // Token is read from localStorage in request interceptor
  },
};

api.interceptors.request.use((config) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);
