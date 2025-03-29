import { apiClient } from "@/lib/api-client";
import { setToken, clearToken } from "@/utils/auth";

// Types
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  name: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

// Endpoints
const API_ENDPOINTS = {
  TOKEN: "/api/v1/auth/token",
  REGISTER: "/api/v1/auth/register",
  REFRESH: "/api/v1/auth/refresh-token",
};

// Auth Service
export const authService = {
  /**
   * Login user with email and password
   */
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}${API_ENDPOINTS.TOKEN}`, 
      {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          grant_type: 'password',
          username: credentials.email,
          password: credentials.password,
          scope: '',
          client_id: process.env.NEXT_PUBLIC_CLIENT_ID || 'string',
          client_secret: process.env.NEXT_PUBLIC_CLIENT_SECRET || 'string',
        }),
      }
    );
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to sign in');
    }

    const data: AuthResponse = await response.json();
    
    // Store the token
    setToken(data.access_token);
    
    // Also store in sessionStorage as a backup
    if (typeof window !== 'undefined') {
      try {
        sessionStorage.setItem('accessToken', data.access_token);
        sessionStorage.setItem('auth_timestamp', Date.now().toString());
      } catch (e) {
        console.error('Failed to store in sessionStorage:', e);
      }
    }
    
    return data;
  },
  
  /**
   * Register a new user
   */
  register: async (data: RegisterData): Promise<void> => {
    const response = await apiClient.post(
      API_ENDPOINTS.REGISTER,
      {
        name: data.name,
        email: data.email,
        password: data.password,
      }
    );
    
    if (response.error) {
      throw new Error(response.error || 'Registration failed');
    }
  },
  
  /**
   * Logout the current user
   */
  logout: (): void => {
    clearToken();
    
    // Also clear from sessionStorage
    if (typeof window !== 'undefined') {
      try {
        sessionStorage.removeItem('accessToken');
        sessionStorage.removeItem('auth_timestamp');
      } catch (e) {
        console.error('Failed to clear sessionStorage:', e);
      }
    }
  },
  
  /**
   * Refresh the auth token
   */
  refreshToken: async (): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>(API_ENDPOINTS.REFRESH);
    
    if (response.error) {
      throw new Error(response.error || 'Failed to refresh token');
    }
    
    // Store the new token
    setToken(response.data.access_token);
    
    return response.data;
  }
};

export default authService; 