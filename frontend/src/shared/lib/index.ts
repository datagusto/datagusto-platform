/**
 * Shared library barrel export
 *
 * @description Centralizes exports for library configurations and utilities.
 * Includes TanStack Query client, API client, and helper functions.
 *
 * @example
 * ```typescript
 * import { queryClient, apiClient, cn } from '@/shared/lib';
 * ```
 */

// TanStack Query client and utilities
export {
  queryClient,
  invalidateQueries,
  prefetchQuery,
  setQueryData,
  getQueryData,
} from './query-client';

// API client and utilities
export {
  apiClient,
  ApiError,
  get,
  post,
  put,
  patch,
  del,
  type ApiClientOptions,
} from './api-client';

// Export utilities
export { cn } from './utils';
