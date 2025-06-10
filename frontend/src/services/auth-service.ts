import type { LoginCredentials, RegisterData, TokenResponse, User, ApiError } from '@/types/auth';

/**
 * Simple and clean authentication service
 * Matches the backend API specification exactly
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL;
const API_VERSION = process.env.NEXT_PUBLIC_API_VERSION || 'v1';

// Helper function to handle API responses
async function handleApiResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData: ApiError = await response.json();
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

// Helper function to get token from localStorage
function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

// Helper function to store token in localStorage
function storeToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('access_token', token);
}

// Helper function to clear token from localStorage
function clearStoredToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('access_token');
}

export const authService = {
  /**
   * Login with email and password
   * Returns JWT token on success
   */
  async login(credentials: LoginCredentials): Promise<TokenResponse> {
    const response = await fetch(`${API_BASE}/api/${API_VERSION}/auth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        username: credentials.email,
        password: credentials.password,
      }),
    });

    const tokenResponse = await handleApiResponse<TokenResponse>(response);
    storeToken(tokenResponse.access_token);
    return tokenResponse;
  },

  /**
   * Register a new user
   * Returns user data on success
   */
  async register(userData: RegisterData): Promise<User> {
    const response = await fetch(`${API_BASE}/api/${API_VERSION}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    return handleApiResponse<User>(response);
  },

  /**
   * Get current user information
   * Requires valid token
   */
  async getCurrentUser(): Promise<User> {
    const token = getStoredToken();
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${API_BASE}/api/${API_VERSION}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    return handleApiResponse<User>(response);
  },

  /**
   * Logout current user
   * Clears stored token
   */
  logout(): void {
    clearStoredToken();
  },

  /**
   * Check if user is authenticated
   * Returns true if valid token exists
   */
  isAuthenticated(): boolean {
    return !!getStoredToken();
  },

  /**
   * Get current token
   */
  getToken(): string | null {
    return getStoredToken();
  },
}; 