/**
 * API configuration
 *
 * @description Centralizes all API-related configuration including base URLs,
 * version, timeout settings, and other API client options. Values are read from
 * environment variables with sensible defaults for development.
 *
 * **Environment Variables**:
 * - `NEXT_PUBLIC_API_URL`: Backend API base URL (default: http://localhost:8000)
 * - `NEXT_PUBLIC_API_VERSION`: API version prefix (default: v1)
 *
 * @module api.config
 */

/**
 * API configuration object
 *
 * @description Contains all configuration values for API communication.
 * These values are used by the API client to construct requests.
 *
 * **Configuration Options**:
 * - **BASE_URL**: Full URL to the backend API server
 * - **VERSION**: API version (e.g., "v1") used in endpoint paths
 * - **TIMEOUT**: Request timeout in milliseconds before failing
 * - **RETRY_COUNT**: Number of times to retry failed requests
 * - **RETRY_DELAY**: Base delay in milliseconds between retries (exponential backoff)
 *
 * @example
 * ```typescript
 * import { API_CONFIG } from '@/shared/config';
 *
 * // Construct API endpoint
 * const endpoint = `${API_CONFIG.BASE_URL}/api/${API_CONFIG.VERSION}/users`;
 * console.log(endpoint); // http://localhost:8000/api/v1/users
 * ```
 *
 * @example
 * ```typescript
 * // Use in fetch call
 * const response = await fetch(
 *   `${API_CONFIG.BASE_URL}/api/${API_CONFIG.VERSION}/auth/me`,
 *   {
 *     signal: AbortSignal.timeout(API_CONFIG.TIMEOUT),
 *   }
 * );
 * ```
 */
export const API_CONFIG = {
  /**
   * Backend API base URL
   *
   * @description Read from NEXT_PUBLIC_API_URL environment variable.
   * Defaults to http://localhost:8000 for local development.
   *
   * **Production**: Set this to your production API URL
   * **Staging**: Set this to your staging API URL
   * **Development**: Default localhost:8000 works with typical backend setup
   */
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',

  /**
   * API version prefix
   *
   * @description Read from NEXT_PUBLIC_API_VERSION environment variable.
   * Defaults to "v1". Used in endpoint paths like `/api/v1/users`.
   *
   * **Note**: Changing this affects all API endpoints. Ensure backend matches.
   */
  VERSION: process.env.NEXT_PUBLIC_API_VERSION || 'v1',

  /**
   * Request timeout in milliseconds
   *
   * @description Maximum time to wait for API response before aborting.
   * Default: 30000ms (30 seconds)
   *
   * **Adjust based on**:
   * - Network conditions (slower networks may need longer timeout)
   * - Endpoint complexity (heavy queries may need longer timeout)
   * - User experience requirements (shorter timeout = faster failure feedback)
   */
  TIMEOUT: 30000, // 30 seconds

  /**
   * Number of retry attempts for failed requests
   *
   * @description How many times to retry a failed request before giving up.
   * Default: 1 (try once more after initial failure)
   *
   * **Use cases**:
   * - Network glitches (temporary connection loss)
   * - Server temporary unavailability (502, 503 errors)
   * - Rate limiting (429 errors)
   */
  RETRY_COUNT: 1,

  /**
   * Base delay between retries in milliseconds
   *
   * @description Initial delay before first retry. Subsequent retries use exponential backoff.
   * Default: 1000ms (1 second)
   *
   * **Exponential backoff formula**:
   * - 1st retry: RETRY_DELAY * 1 = 1000ms
   * - 2nd retry: RETRY_DELAY * 2 = 2000ms
   * - 3rd retry: RETRY_DELAY * 4 = 4000ms
   */
  RETRY_DELAY: 1000, // 1 second
} as const;

/**
 * API endpoint paths
 *
 * @description Centralized endpoint path definitions for type-safe API calls.
 * Helps prevent typos and makes endpoint changes easier to manage.
 *
 * @example
 * ```typescript
 * import { API_ENDPOINTS } from '@/shared/config';
 *
 * const response = await apiClient(API_ENDPOINTS.AUTH.ME);
 * ```
 */
export const API_ENDPOINTS = {
  /**
   * Authentication endpoints
   */
  AUTH: {
    /** POST /api/v1/auth/token - Login with email/password */
    TOKEN: '/auth/token',

    /** POST /api/v1/auth/register - Register new user */
    REGISTER: '/auth/register',

    /** GET /api/v1/auth/me - Get current user info */
    ME: '/auth/me',

    /** POST /api/v1/auth/refresh - Refresh access token */
    REFRESH: '/auth/refresh',

    /** POST /api/v1/auth/logout - Logout (invalidate token) */
    LOGOUT: '/auth/logout',
  },

  /**
   * Project endpoints (future)
   */
  PROJECTS: {
    /** GET /api/v1/projects - List projects */
    LIST: '/projects',

    /** GET /api/v1/projects/:id - Get project by ID */
    DETAIL: (id: string) => `/projects/${id}`,

    /** POST /api/v1/projects - Create project */
    CREATE: '/projects',

    /** PUT /api/v1/projects/:id - Update project */
    UPDATE: (id: string) => `/projects/${id}`,

    /** DELETE /api/v1/projects/:id - Delete project */
    DELETE: (id: string) => `/projects/${id}`,
  },
} as const;

/**
 * HTTP status codes for common API responses
 *
 * @description Enum-like object for HTTP status codes.
 * Use these constants instead of magic numbers for better code readability.
 *
 * @example
 * ```typescript
 * if (response.status === HTTP_STATUS.UNAUTHORIZED) {
 *   // Handle unauthorized
 * }
 * ```
 */
export const HTTP_STATUS = {
  /** Request succeeded */
  OK: 200,

  /** Resource created */
  CREATED: 201,

  /** Request accepted but not yet processed */
  ACCEPTED: 202,

  /** Success with no content to return */
  NO_CONTENT: 204,

  /** Bad request (validation error, malformed request) */
  BAD_REQUEST: 400,

  /** Authentication required */
  UNAUTHORIZED: 401,

  /** Authenticated but not authorized for this resource */
  FORBIDDEN: 403,

  /** Resource not found */
  NOT_FOUND: 404,

  /** Request method not allowed for this endpoint */
  METHOD_NOT_ALLOWED: 405,

  /** Request conflicts with current state (e.g., duplicate email) */
  CONFLICT: 409,

  /** Request entity too large */
  PAYLOAD_TOO_LARGE: 413,

  /** Too many requests (rate limiting) */
  TOO_MANY_REQUESTS: 429,

  /** Internal server error */
  INTERNAL_SERVER_ERROR: 500,

  /** Service unavailable (maintenance, overload) */
  SERVICE_UNAVAILABLE: 503,

  /** Gateway timeout */
  GATEWAY_TIMEOUT: 504,
} as const;
