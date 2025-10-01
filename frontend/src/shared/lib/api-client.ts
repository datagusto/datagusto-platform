/**
 * API client for HTTP requests
 *
 * @description Centralized HTTP client for all API communication.
 * Handles authentication, error handling, timeouts, and retries automatically.
 *
 * **Features**:
 * - Automatic authentication header injection from Zustand store
 * - Type-safe request/response handling
 * - Automatic retry logic with exponential backoff
 * - Request timeout handling
 * - Standardized error handling
 * - Support for all HTTP methods (GET, POST, PUT, DELETE, PATCH)
 *
 * @module api-client
 */

import { useAuthStore } from '@/features/auth/stores';
import { API_CONFIG, HTTP_STATUS } from '@/shared/config/api.config';

/**
 * Custom API error class
 *
 * @class ApiError
 * @extends Error
 * @description Enhanced error class for API-related errors with additional context.
 * Includes HTTP status code, response data, and original request information.
 *
 * @property {number} status - HTTP status code (e.g., 404, 500)
 * @property {any} data - Error response data from API (if available)
 * @property {string} endpoint - API endpoint that failed
 *
 * @example
 * ```typescript
 * try {
 *   await apiClient('/auth/me');
 * } catch (error) {
 *   if (error instanceof ApiError) {
 *     console.error('API Error:', error.status, error.message);
 *     console.error('Endpoint:', error.endpoint);
 *     console.error('Details:', error.data);
 *   }
 * }
 * ```
 */
export class ApiError extends Error {
  /**
   * Creates an API error
   *
   * @param message - Error message
   * @param status - HTTP status code
   * @param data - Response data from API
   * @param endpoint - API endpoint that failed
   */
  constructor(
    message: string,
    public status: number,
    public data?: unknown,
    public endpoint?: string
  ) {
    super(message);
    this.name = 'ApiError';

    // Maintains proper stack trace for debugging (only available on V8)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ApiError);
    }
  }
}

/**
 * API client options
 *
 * @interface ApiClientOptions
 * @description Configuration options for individual API requests.
 * Extends standard fetch RequestInit with additional options.
 *
 * @property {boolean} [skipAuth] - Skip automatic auth header injection
 * @property {number} [timeout] - Custom timeout in milliseconds (overrides default)
 * @property {number} [retries] - Number of retry attempts (overrides default)
 * @property {boolean} [skipRetry] - Skip retry logic completely
 */
export interface ApiClientOptions extends RequestInit {
  /** Skip automatic authentication header injection (for public endpoints) */
  skipAuth?: boolean;

  /** Custom timeout in milliseconds (overrides API_CONFIG.TIMEOUT) */
  timeout?: number;

  /** Number of retry attempts (overrides API_CONFIG.RETRY_COUNT) */
  retries?: number;

  /** Skip retry logic completely (fail immediately on error) */
  skipRetry?: boolean;
}

/**
 * Delay execution for specified milliseconds
 *
 * @description Helper function for implementing retry delays.
 * Uses exponential backoff: delay * (2 ^ attempt)
 *
 * @param ms - Milliseconds to delay
 * @returns Promise that resolves after delay
 *
 * @example
 * ```typescript
 * await delay(1000); // Wait 1 second
 * ```
 */
function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Core API client function
 *
 * @description Makes HTTP requests to the backend API with automatic:
 * - Authentication (adds Bearer token from Zustand store)
 * - Error handling (converts responses to ApiError)
 * - Timeout handling (aborts request after timeout)
 * - Retry logic (retries on network/server errors)
 * - JSON serialization/deserialization
 *
 * **Usage Pattern**:
 * 1. Use directly for simple requests
 * 2. Wrap in service functions for feature-specific API calls
 * 3. Integrate with TanStack Query for caching and state management
 *
 * **Authentication**:
 * - Automatically injects `Authorization: Bearer <token>` header
 * - Token retrieved from Zustand store (useAuthStore)
 * - Skip auth with `skipAuth: true` option for public endpoints
 *
 * **Error Handling**:
 * - HTTP errors (4xx, 5xx) throw ApiError with status and message
 * - Network errors throw ApiError with status 0
 * - Timeout errors throw ApiError with message "Request timeout"
 *
 * **Retry Logic**:
 * - Retries on network errors and 5xx server errors
 * - Does NOT retry on 4xx client errors (bad request, unauthorized, etc.)
 * - Uses exponential backoff: 1s, 2s, 4s, etc.
 * - Can be disabled with `skipRetry: true`
 *
 * @template T - Expected response data type
 * @param endpoint - API endpoint path (e.g., "/auth/me")
 * @param options - Request options including method, body, headers, etc.
 * @returns Promise resolving to typed response data
 * @throws {ApiError} When request fails, times out, or returns error status
 *
 * @example
 * ```typescript
 * // Simple GET request
 * const user = await apiClient<User>('/auth/me');
 * console.log(user.email);
 * ```
 *
 * @example
 * ```typescript
 * // POST request with body
 * const newProject = await apiClient<Project>('/projects', {
 *   method: 'POST',
 *   body: JSON.stringify({ name: 'My Project' }),
 * });
 * ```
 *
 * @example
 * ```typescript
 * // Public endpoint (skip auth)
 * const publicData = await apiClient('/public/stats', {
 *   skipAuth: true,
 * });
 * ```
 *
 * @example
 * ```typescript
 * // Custom timeout and retry
 * const data = await apiClient('/slow-endpoint', {
 *   timeout: 60000, // 60 seconds
 *   retries: 3, // Retry 3 times
 * });
 * ```
 *
 * @example
 * ```typescript
 * // Error handling
 * try {
 *   const data = await apiClient('/auth/me');
 * } catch (error) {
 *   if (error instanceof ApiError) {
 *     if (error.status === 401) {
 *       // Handle unauthorized (redirect to login)
 *     } else if (error.status === 404) {
 *       // Handle not found
 *     } else {
 *       // Handle other errors
 *     }
 *   }
 * }
 * ```
 */
export async function apiClient<T>(
  endpoint: string,
  options: ApiClientOptions = {}
): Promise<T> {
  const {
    skipAuth = false,
    timeout = API_CONFIG.TIMEOUT,
    retries = API_CONFIG.RETRY_COUNT,
    skipRetry = false,
    ...fetchOptions
  } = options;

  // Construct full URL
  const url = `${API_CONFIG.BASE_URL}/api/${API_CONFIG.VERSION}${endpoint}`;

  // Get auth token and organization ID from Zustand store (outside React component)
  const token = useAuthStore.getState().token;
  const organizationId = useAuthStore.getState().currentOrganizationId;

  // Prepare headers
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(fetchOptions.headers as Record<string, string>),
  };

  // Add authentication header if token exists and not skipped
  if (token && !skipAuth) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Add organization context header if available
  // Backend middleware gives this precedence over token org_id
  if (organizationId && !skipAuth) {
    headers['X-Organization-ID'] = organizationId;
  }

  // Create abort controller for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  // Retry logic
  let lastError: Error | null = null;
  const maxAttempts = skipRetry ? 1 : retries + 1;

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      // Make fetch request
      const response = await fetch(url, {
        ...fetchOptions,
        headers,
        signal: controller.signal,
      });

      // Clear timeout
      clearTimeout(timeoutId);

      // Handle error responses
      if (!response.ok) {
        // Try to parse error response
        let errorData: unknown;
        let errorMessage = `HTTP ${response.status}`;

        try {
          errorData = await response.json();
          if (
            errorData &&
            typeof errorData === 'object' &&
            ('detail' in errorData || 'message' in errorData)
          ) {
            const err = errorData as { detail?: string; message?: string };
            errorMessage = err.detail || err.message || errorMessage;
          }
        } catch {
          // Response is not JSON, use status text
          errorMessage = response.statusText || errorMessage;
        }

        // Create ApiError
        const error = new ApiError(
          errorMessage,
          response.status,
          errorData,
          endpoint
        );

        // Handle 401 Unauthorized - attempt token refresh
        if (response.status === HTTP_STATUS.UNAUTHORIZED && !skipAuth && endpoint !== '/auth/refresh') {
          const refreshToken = useAuthStore.getState().refreshToken;

          if (refreshToken) {
            try {
              // Attempt to refresh the access token
              const refreshResponse = await fetch(
                `${API_CONFIG.BASE_URL}/api/${API_CONFIG.VERSION}/auth/refresh`,
                {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                  },
                  body: JSON.stringify({ refresh_token: refreshToken }),
                }
              );

              if (refreshResponse.ok) {
                const { access_token } = await refreshResponse.json();

                // Update token in store
                useAuthStore.getState().setToken(access_token);

                // Retry original request with new token
                headers['Authorization'] = `Bearer ${access_token}`;
                const retryResponse = await fetch(url, {
                  ...fetchOptions,
                  headers,
                  signal: controller.signal,
                });

                if (retryResponse.ok) {
                  // Clear timeout
                  clearTimeout(timeoutId);

                  // Handle No Content response (204)
                  if (retryResponse.status === HTTP_STATUS.NO_CONTENT) {
                    return undefined as T;
                  }

                  // Parse JSON response
                  const data = await retryResponse.json();
                  return data as T;
                }
              }
            } catch (refreshError) {
              // Refresh failed, clear auth and redirect to login
              useAuthStore.getState().clearAuth();
              if (typeof window !== 'undefined') {
                window.location.href = '/sign-in';
              }
              throw error;
            }
          }

          // No refresh token or refresh failed, clear auth and redirect to login
          useAuthStore.getState().clearAuth();
          if (typeof window !== 'undefined') {
            window.location.href = '/sign-in';
          }
          throw error;
        }

        // Don't retry on 4xx client errors (except 429 Too Many Requests)
        if (
          response.status >= 400 &&
          response.status < 500 &&
          response.status !== HTTP_STATUS.TOO_MANY_REQUESTS
        ) {
          throw error;
        }

        // Retry on 5xx server errors and 429
        lastError = error;

        // If this is not the last attempt, wait and retry
        if (attempt < maxAttempts - 1) {
          const delayMs = API_CONFIG.RETRY_DELAY * Math.pow(2, attempt);
          await delay(delayMs);
          continue;
        }

        // Last attempt failed, throw error
        throw error;
      }

      // Handle No Content response (204)
      if (response.status === HTTP_STATUS.NO_CONTENT) {
        return undefined as T;
      }

      // Parse JSON response
      const data = await response.json();
      return data as T;
    } catch (error) {
      // Clear timeout
      clearTimeout(timeoutId);

      // Handle abort error (timeout)
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ApiError('Request timeout', 0, { timeout }, endpoint);
      }

      // If it's already an ApiError, just re-throw or retry
      if (error instanceof ApiError) {
        lastError = error;

        // If this is not the last attempt and it's a retryable error, wait and retry
        if (attempt < maxAttempts - 1 && error.status >= 500) {
          const delayMs = API_CONFIG.RETRY_DELAY * Math.pow(2, attempt);
          await delay(delayMs);
          continue;
        }

        // Last attempt or non-retryable error, throw
        throw error;
      }

      // Handle network errors
      if (error instanceof Error) {
        lastError = error;

        // If this is not the last attempt, wait and retry
        if (attempt < maxAttempts - 1) {
          const delayMs = API_CONFIG.RETRY_DELAY * Math.pow(2, attempt);
          await delay(delayMs);
          continue;
        }

        // Last attempt failed, throw ApiError
        throw new ApiError(
          error.message || 'Network error',
          0,
          { originalError: error },
          endpoint
        );
      }

      // Unknown error type
      throw new ApiError(
        'Unknown error',
        0,
        { originalError: error },
        endpoint
      );
    }
  }

  // This should never be reached, but TypeScript requires it
  throw lastError || new ApiError('Request failed', 0, undefined, endpoint);
}

/**
 * Helper function for GET requests
 *
 * @description Convenience wrapper for GET requests.
 * Equivalent to `apiClient(endpoint, { method: 'GET' })`
 *
 * @template T - Expected response data type
 * @param endpoint - API endpoint path
 * @param options - Request options
 * @returns Promise resolving to typed response data
 *
 * @example
 * ```typescript
 * const users = await get<User[]>('/users');
 * ```
 */
export function get<T>(
  endpoint: string,
  options?: ApiClientOptions
): Promise<T> {
  return apiClient<T>(endpoint, { ...options, method: 'GET' });
}

/**
 * Helper function for POST requests
 *
 * @description Convenience wrapper for POST requests with JSON body.
 * Automatically stringifies body data.
 *
 * @template T - Expected response data type
 * @param endpoint - API endpoint path
 * @param data - Request body data (will be JSON.stringify'd)
 * @param options - Request options
 * @returns Promise resolving to typed response data
 *
 * @example
 * ```typescript
 * const newUser = await post<User>('/users', {
 *   name: 'John Doe',
 *   email: 'john@example.com',
 * });
 * ```
 */
export function post<T>(
  endpoint: string,
  data?: unknown,
  options?: ApiClientOptions
): Promise<T> {
  return apiClient<T>(endpoint, {
    ...options,
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  });
}

/**
 * Helper function for PUT requests
 *
 * @description Convenience wrapper for PUT requests with JSON body.
 * Automatically stringifies body data.
 *
 * @template T - Expected response data type
 * @param endpoint - API endpoint path
 * @param data - Request body data (will be JSON.stringify'd)
 * @param options - Request options
 * @returns Promise resolving to typed response data
 *
 * @example
 * ```typescript
 * const updatedUser = await put<User>('/users/123', {
 *   name: 'Jane Doe',
 * });
 * ```
 */
export function put<T>(
  endpoint: string,
  data?: unknown,
  options?: ApiClientOptions
): Promise<T> {
  return apiClient<T>(endpoint, {
    ...options,
    method: 'PUT',
    body: data ? JSON.stringify(data) : undefined,
  });
}

/**
 * Helper function for PATCH requests
 *
 * @description Convenience wrapper for PATCH requests with JSON body.
 * Automatically stringifies body data.
 *
 * @template T - Expected response data type
 * @param endpoint - API endpoint path
 * @param data - Request body data (will be JSON.stringify'd)
 * @param options - Request options
 * @returns Promise resolving to typed response data
 *
 * @example
 * ```typescript
 * const updatedUser = await patch<User>('/users/123', {
 *   name: 'Jane Doe', // Only update name
 * });
 * ```
 */
export function patch<T>(
  endpoint: string,
  data?: unknown,
  options?: ApiClientOptions
): Promise<T> {
  return apiClient<T>(endpoint, {
    ...options,
    method: 'PATCH',
    body: data ? JSON.stringify(data) : undefined,
  });
}

/**
 * Helper function for DELETE requests
 *
 * @description Convenience wrapper for DELETE requests.
 *
 * @template T - Expected response data type
 * @param endpoint - API endpoint path
 * @param options - Request options
 * @returns Promise resolving to typed response data
 *
 * @example
 * ```typescript
 * await del('/users/123'); // Delete user
 * ```
 */
export function del<T = void>(
  endpoint: string,
  options?: ApiClientOptions
): Promise<T> {
  return apiClient<T>(endpoint, { ...options, method: 'DELETE' });
}
