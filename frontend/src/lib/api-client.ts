/**
 * API client with automatic token refresh
 */
import { authService } from '@/services/auth-service';

const API_BASE = process.env.NEXT_PUBLIC_API_URL;
const API_VERSION = process.env.NEXT_PUBLIC_API_VERSION || 'v1';

let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

// Subscribe to token refresh
function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

// Notify all subscribers when token is refreshed
function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach(cb => cb(token));
  refreshSubscribers = [];
}

// Parse JWT token to check expiration
function parseJwt(token: string): any {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch {
    return null;
  }
}

// Check if token is expired or about to expire (within 5 minutes)
function isTokenExpired(token: string): boolean {
  const payload = parseJwt(token);
  if (!payload || !payload.exp) return true;
  
  const expirationTime = payload.exp * 1000; // Convert to milliseconds
  const currentTime = Date.now();
  const timeUntilExpiry = expirationTime - currentTime;
  
  // Consider token expired if it expires within 5 minutes
  return timeUntilExpiry < 5 * 60 * 1000;
}

// Refresh token and retry request
async function refreshTokenAndRetryRequest(originalRequest: RequestInfo | URL, options?: RequestInit): Promise<Response> {
  if (!isRefreshing) {
    isRefreshing = true;
    
    try {
      const tokenResponse = await authService.refreshToken();
      const newToken = tokenResponse.access_token;
      isRefreshing = false;
      onTokenRefreshed(newToken);
      
      // Retry original request with new token
      const newOptions = {
        ...options,
        headers: {
          ...options?.headers,
          'Authorization': `Bearer ${newToken}`,
        },
      };
      return fetch(originalRequest, newOptions);
    } catch (error) {
      isRefreshing = false;
      // Refresh failed, logout user
      authService.logout();
      if (typeof window !== 'undefined') {
        window.location.href = '/sign-in';
      }
      throw error;
    }
  }
  
  // Wait for token refresh to complete
  return new Promise((resolve) => {
    subscribeTokenRefresh((token: string) => {
      const newOptions = {
        ...options,
        headers: {
          ...options?.headers,
          'Authorization': `Bearer ${token}`,
        },
      };
      resolve(fetch(originalRequest, newOptions));
    });
  });
}

/**
 * Enhanced fetch function with automatic token refresh
 */
export async function apiFetch(path: string, options?: RequestInit): Promise<Response> {
  const url = `${API_BASE}/api/${API_VERSION}${path}`;
  const token = authService.getToken();
  
  // Check if token needs refresh before making request
  if (token && isTokenExpired(token)) {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      return refreshTokenAndRetryRequest(url, options);
    }
  }
  
  // Add authorization header if token exists
  const requestOptions: RequestInit = {
    ...options,
    headers: {
      ...options?.headers,
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
  };
  
  const response = await fetch(url, requestOptions);
  
  // If response is 401, try to refresh token
  if (response.status === 401 && token) {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken && !isRefreshing) {
      return refreshTokenAndRetryRequest(url, options);
    }
  }
  
  return response;
}

/**
 * API client helper methods
 */
export const apiClient = {
  async get<T>(path: string): Promise<T> {
    const response = await apiFetch(path);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return response.json();
  },

  async post<T>(path: string, data?: any): Promise<T> {
    const response = await apiFetch(path, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return response.json();
  },

  async put<T>(path: string, data?: any): Promise<T> {
    const response = await apiFetch(path, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return response.json();
  },

  async delete<T>(path: string): Promise<T> {
    const response = await apiFetch(path, {
      method: 'DELETE',
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return response.json();
  },
};