/**
 * Authentication service
 *
 * @description Handles all authentication-related API calls including login, registration,
 * user data retrieval, and token management. Integrates with Zustand store for state management.
 *
 * **Architecture**:
 * - Uses new apiClient for most endpoints (automatic auth, retry, timeout)
 * - Direct fetch for login endpoint (requires application/x-www-form-urlencoded)
 * - Token storage delegated to Zustand store (no direct localStorage manipulation)
 * - Type-safe with comprehensive error handling
 *
 * @module auth.service
 */

import { apiClient, ApiError, post } from '@/shared/lib';
import { API_CONFIG, API_ENDPOINTS } from '@/shared/config';
import { useAuthStore } from '../stores';
import type {
  LoginCredentials,
  RegisterData,
  User,
  TokenResponse,
} from '../types';

/**
 * Authentication service object
 *
 * @description Centralized authentication API methods.
 * All methods are async and return Promises for integration with TanStack Query.
 *
 * **Token Management**:
 * - Tokens are stored in Zustand store (not directly in localStorage)
 * - Use `useAuthStore.getState().setAuth()` to store tokens
 * - Use `useAuthStore.getState().clearAuth()` to clear tokens
 *
 * **Error Handling**:
 * - All methods throw ApiError on failure
 * - ApiError includes HTTP status code and error message
 * - Integrate with TanStack Query for automatic retry and error states
 *
 * @example
 * ```typescript
 * // Direct usage (not recommended, use hooks instead)
 * try {
 *   const tokens = await authService.login({
 *     email: 'user@example.com',
 *     password: 'password123',
 *   });
 *   console.log('Logged in:', tokens);
 * } catch (error) {
 *   if (error instanceof ApiError) {
 *     console.error('Login failed:', error.message);
 *   }
 * }
 * ```
 *
 * @example
 * ```typescript
 * // Recommended: Use with TanStack Query hooks
 * import { useMutation } from '@tanstack/react-query';
 *
 * function LoginForm() {
 *   const loginMutation = useMutation({
 *     mutationFn: authService.login,
 *   });
 *
 *   const handleSubmit = (data) => {
 *     loginMutation.mutate(data);
 *   };
 * }
 * ```
 */
export const authService = {
  /**
   * Authenticates user with email and password
   *
   * @description Sends login credentials to backend and receives JWT tokens.
   * On success, stores tokens in Zustand store and returns token response.
   *
   * **Backend Endpoint**: POST /api/v1/auth/token
   *
   * **Content-Type**: application/x-www-form-urlencoded (OAuth2 standard)
   * - Username field contains email address
   * - Password field contains plain-text password (encrypted in transit via HTTPS)
   *
   * **Flow**:
   * 1. Send credentials to backend API
   * 2. Receive access_token and refresh_token
   * 3. Store tokens in Zustand store (NOT done here, delegate to hooks)
   * 4. Return token response for further processing
   *
   * **Security Note**:
   * - Password sent as plain text (HTTPS encrypts in transit)
   * - Backend hashes password before comparing with database
   * - JWT tokens are signed and expire after configured time
   *
   * @param credentials - User login credentials
   * @param credentials.email - User's email address
   * @param credentials.password - User's password (plain text)
   * @returns Promise resolving to TokenResponse with access_token and refresh_token
   * @throws {ApiError} When authentication fails (invalid credentials, network error, etc.)
   *
   * @example
   * ```typescript
   * // Login user
   * const tokens = await authService.login({
   *   email: 'user@example.com',
   *   password: 'securePassword123',
   * });
   *
   * console.log('Access token:', tokens.access_token);
   * console.log('Refresh token:', tokens.refresh_token);
   * console.log('Token type:', tokens.token_type); // 'bearer'
   * ```
   *
   * @example
   * ```typescript
   * // Error handling
   * try {
   *   await authService.login(credentials);
   * } catch (error) {
   *   if (error instanceof ApiError) {
   *     if (error.status === 401) {
   *       console.error('Invalid email or password');
   *     } else if (error.status === 429) {
   *       console.error('Too many login attempts, try again later');
   *     } else {
   *       console.error('Login error:', error.message);
   *     }
   *   }
   * }
   * ```
   */
  async login(credentials: LoginCredentials): Promise<TokenResponse> {
    // Note: OAuth2 token endpoint requires application/x-www-form-urlencoded
    // Cannot use apiClient which defaults to application/json
    const response = await fetch(
      `${API_CONFIG.BASE_URL}/api/${API_CONFIG.VERSION}${API_ENDPOINTS.AUTH.TOKEN}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          username: credentials.email, // OAuth2 spec uses 'username' field
          password: credentials.password,
        }),
      }
    );

    // Handle error responses
    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        // Response is not JSON, use status text
        errorMessage = response.statusText || errorMessage;
      }

      throw new ApiError(
        errorMessage,
        response.status,
        undefined,
        API_ENDPOINTS.AUTH.TOKEN
      );
    }

    // Parse and return token response
    const tokenResponse = await response.json();
    return tokenResponse as TokenResponse;
  },

  /**
   * Registers a new user account
   *
   * @description Creates a new user in the system with provided registration data.
   * Returns authentication tokens that can be used to immediately log in the user.
   *
   * **Backend Endpoint**: POST /api/v1/auth/register
   *
   * **Content-Type**: application/json
   *
   * **Flow**:
   * 1. Submit registration data (name, email, password)
   * 2. Backend validates data and creates user
   * 3. Backend returns access token, refresh token, and user data
   * 4. Frontend can store tokens and log user in automatically
   *
   * **Validation**:
   * - Email must be unique (backend checks)
   * - Password must meet security requirements (backend enforces)
   * - Name can be any string (min 2 characters validated client-side)
   *
   * @param userData - New user registration data
   * @param userData.name - User's display name
   * @param userData.email - User's email address (must be unique)
   * @param userData.password - User's chosen password
   * @returns Promise resolving to TokenResponse with tokens and user data
   * @throws {ApiError} When registration fails (duplicate email, validation error, etc.)
   *
   * @example
   * ```typescript
   * // Register new user and receive tokens
   * const response = await authService.register({
   *   name: 'John Doe',
   *   email: 'john@example.com',
   *   password: 'securePassword123',
   * });
   *
   * console.log('User created:', response.user_id);
   * console.log('Email:', response.email);
   * console.log('Access token:', response.access_token);
   * console.log('Refresh token:', response.refresh_token);
   * ```
   *
   * @example
   * ```typescript
   * // Error handling
   * try {
   *   await authService.register(userData);
   * } catch (error) {
   *   if (error instanceof ApiError) {
   *     if (error.status === 409) {
   *       console.error('Email already registered');
   *     } else if (error.status === 400) {
   *       console.error('Validation error:', error.message);
   *     } else {
   *       console.error('Registration error:', error.message);
   *     }
   *   }
   * }
   * ```
   */
  async register(userData: RegisterData): Promise<TokenResponse> {
    // Use apiClient's post helper (automatic JSON, error handling, retry)
    return post<TokenResponse>(API_ENDPOINTS.AUTH.REGISTER, userData);
  },

  /**
   * Retrieves current authenticated user's data
   *
   * @description Fetches detailed information about the currently logged-in user.
   * Requires valid authentication token in Zustand store.
   *
   * **Backend Endpoint**: GET /api/v1/auth/me
   *
   * **Authentication**: Requires Bearer token in Authorization header
   * (automatically added by apiClient)
   *
   * **Use Cases**:
   * - Verify token validity
   * - Display user profile information
   * - Check user permissions/roles
   * - Refresh user data after updates
   *
   * **Caching**:
   * - Integrate with TanStack Query for automatic caching
   * - Set appropriate staleTime (e.g., 5 minutes)
   * - Invalidate cache after profile updates
   *
   * @returns Promise resolving to User object with full profile data
   * @throws {ApiError} When not authenticated or token expired (401)
   * @throws {ApiError} When network error or server error occurs
   *
   * @example
   * ```typescript
   * // Get current user
   * const user = await authService.getCurrentUser();
   *
   * console.log('User ID:', user.id);
   * console.log('Email:', user.email);
   * console.log('Name:', user.name);
   * console.log('Active:', user.is_active);
   * console.log('Email confirmed:', user.email_confirmed);
   * ```
   *
   * @example
   * ```typescript
   * // With TanStack Query (recommended)
   * import { useQuery } from '@tanstack/react-query';
   *
   * function useCurrentUser() {
   *   return useQuery({
   *     queryKey: ['currentUser'],
   *     queryFn: () => authService.getCurrentUser(),
   *     staleTime: 5 * 60 * 1000, // 5 minutes
   *     retry: 1,
   *   });
   * }
   * ```
   *
   * @example
   * ```typescript
   * // Error handling (token expired)
   * try {
   *   const user = await authService.getCurrentUser();
   * } catch (error) {
   *   if (error instanceof ApiError && error.status === 401) {
   *     // Token expired, logout user
   *     useAuthStore.getState().clearAuth();
   *     router.push('/sign-in');
   *   }
   * }
   * ```
   */
  async getCurrentUser(): Promise<User> {
    // Use apiClient (automatic auth header, retry, timeout)
    return apiClient<User>(API_ENDPOINTS.AUTH.ME);
  },

  /**
   * Refreshes expired access token using refresh token
   *
   * @description Obtains a new access token using the stored refresh token.
   * Called automatically when access token expires (typically after 15-30 minutes).
   *
   * **Backend Endpoint**: POST /api/v1/auth/refresh
   *
   * **Content-Type**: application/json
   *
   * **Flow**:
   * 1. Get refresh token from Zustand store
   * 2. Send refresh token to backend
   * 3. Receive new access token
   * 4. Update Zustand store with new token
   *
   * **Token Lifecycle**:
   * - Access token: Short-lived (15-30 minutes)
   * - Refresh token: Long-lived (7-30 days)
   * - When access token expires, use refresh token to get new one
   * - When refresh token expires, user must login again
   *
   * **Implementation Note**:
   * This method is typically called by an API interceptor or TanStack Query
   * mutation when a 401 Unauthorized response is received.
   *
   * @returns Promise resolving to TokenResponse with new access_token
   * @throws {ApiError} When refresh token is invalid or expired (401)
   * @throws {Error} When no refresh token found in store
   *
   * @example
   * ```typescript
   * // Refresh token manually
   * try {
   *   const tokens = await authService.refreshToken();
   *   useAuthStore.getState().setToken(tokens.access_token);
   * } catch (error) {
   *   // Refresh token expired, logout user
   *   useAuthStore.getState().clearAuth();
   *   router.push('/sign-in');
   * }
   * ```
   *
   * @example
   * ```typescript
   * // Automatic refresh with API interceptor (pseudo-code)
   * async function apiCall(endpoint) {
   *   try {
   *     return await fetch(endpoint);
   *   } catch (error) {
   *     if (error.status === 401) {
   *       // Try refreshing token
   *       await authService.refreshToken();
   *       // Retry original request
   *       return await fetch(endpoint);
   *     }
   *     throw error;
   *   }
   * }
   * ```
   */
  async refreshToken(): Promise<TokenResponse> {
    // Get refresh token from Zustand store
    const refreshToken = useAuthStore.getState().refreshToken;

    if (!refreshToken) {
      throw new Error('No refresh token found');
    }

    // Send refresh token to get new access token
    return post<TokenResponse>(API_ENDPOINTS.AUTH.REFRESH, {
      refresh_token: refreshToken,
    });
  },

  /**
   * Logs out current user
   *
   * @description Clears authentication state from Zustand store.
   * Optionally notifies backend to invalidate tokens (not implemented yet).
   *
   * **Flow**:
   * 1. Clear tokens from Zustand store
   * 2. Clear user data from Zustand store
   * 3. Optionally notify backend to invalidate tokens
   * 4. Redirect to login page
   *
   * **Security Note**:
   * - Frontend logout only clears local state
   * - Backend should implement token blacklist/revocation for full security
   * - Currently, tokens remain valid until expiration even after logout
   *
   * **Implementation Note**:
   * This method only clears local state. Backend logout endpoint
   * (POST /api/v1/auth/logout) should be called separately if token
   * revocation is required.
   *
   * @example
   * ```typescript
   * // Logout user
   * authService.logout();
   * router.push('/sign-in');
   * ```
   *
   * @example
   * ```typescript
   * // Logout with backend notification (future)
   * async function fullLogout() {
   *   try {
   *     // Notify backend to invalidate token
   *     await apiClient(API_ENDPOINTS.AUTH.LOGOUT, { method: 'POST' });
   *   } catch (error) {
   *     // Ignore errors, proceed with local logout
   *     console.warn('Backend logout failed:', error);
   *   } finally {
   *     // Always clear local state
   *     authService.logout();
   *     router.push('/sign-in');
   *   }
   * }
   * ```
   */
  logout(): void {
    // Clear authentication state from Zustand store
    useAuthStore.getState().clearAuth();

    // Future: Notify backend to invalidate token
    // try {
    //   await apiClient(API_ENDPOINTS.AUTH.LOGOUT, { method: 'POST' });
    // } catch (error) {
    //   console.warn('Backend logout failed:', error);
    // }
  },
};
