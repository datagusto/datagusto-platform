/**
 * TanStack Query client configuration
 *
 * @description Configures the global QueryClient for React Query with optimal defaults
 * for caching, retrying, and data synchronization. This client is used throughout
 * the application for all server state management.
 *
 * @module query-client
 */

import { QueryClient } from '@tanstack/react-query';

/**
 * Global QueryClient instance
 *
 * @description Configured with sensible defaults for production use:
 * - **staleTime**: 5 minutes - Data is considered fresh for 5 minutes before refetching
 * - **gcTime**: 10 minutes - Unused data stays in cache for 10 minutes (formerly cacheTime)
 * - **retry**: 1 - Failed queries are retried once before showing error
 * - **refetchOnWindowFocus**: false - Prevents automatic refetch when user returns to tab
 * - **refetchOnReconnect**: true - Refetches data when network connection is restored
 *
 * @example
 * ```tsx
 * // In app/layout.tsx
 * import { QueryClientProvider } from '@tanstack/react-query';
 * import { queryClient } from '@/shared/lib/query-client';
 *
 * export default function RootLayout({ children }) {
 *   return (
 *     <QueryClientProvider client={queryClient}>
 *       {children}
 *     </QueryClientProvider>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Using in a component with useQuery
 * import { useQuery } from '@tanstack/react-query';
 *
 * function MyComponent() {
 *   const { data, isLoading } = useQuery({
 *     queryKey: ['users'],
 *     queryFn: () => fetch('/api/users').then(res => res.json()),
 *   });
 *
 *   return <div>{data?.map(user => user.name)}</div>;
 * }
 * ```
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Data is considered fresh for 5 minutes
      // Prevents unnecessary refetches for recently fetched data
      staleTime: 5 * 60 * 1000, // 5 minutes

      // Garbage collection time - unused data stays in memory for 10 minutes
      // After this time, data is removed from cache if no components are using it
      gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime in v4)

      // Retry failed requests once before showing error
      // Helps handle transient network issues
      retry: 1,

      // Disable automatic refetch when browser window regains focus
      // Reduces unnecessary API calls, especially during development
      refetchOnWindowFocus: false,

      // Refetch data when internet connection is restored
      // Ensures data is fresh after reconnection
      refetchOnReconnect: true,

      // Disable automatic refetch when component mounts if data exists
      // Only refetch if data is stale (based on staleTime)
      refetchOnMount: true,
    },
    mutations: {
      // Retry failed mutations once
      // Useful for handling temporary server errors
      retry: 1,

      // Delay before retrying failed mutation (in milliseconds)
      // Gives server time to recover before retry
      retryDelay: 1000, // 1 second
    },
  },
});

/**
 * Helper function to invalidate specific queries
 *
 * @description Marks queries as stale and triggers refetch for active queries.
 * Useful after mutations to ensure UI shows latest data.
 *
 * @param queryKey - The query key or partial query key to invalidate
 *
 * @example
 * ```typescript
 * // Invalidate all user queries
 * invalidateQueries(['users']);
 *
 * // Invalidate specific user query
 * invalidateQueries(['users', userId]);
 * ```
 */
export function invalidateQueries(queryKey: unknown[]) {
  return queryClient.invalidateQueries({ queryKey });
}

/**
 * Helper function to prefetch data
 *
 * @description Fetches data ahead of time and stores in cache.
 * Useful for improving perceived performance by loading data before user needs it.
 *
 * @param queryKey - The query key to prefetch
 * @param queryFn - The function to fetch data
 * @param staleTime - Optional custom stale time for prefetched data
 *
 * @example
 * ```typescript
 * // Prefetch user data when hovering over profile link
 * function ProfileLink({ userId }) {
 *   const handleMouseEnter = () => {
 *     prefetchQuery(
 *       ['user', userId],
 *       () => api.getUser(userId),
 *       60000 // Keep fresh for 1 minute
 *     );
 *   };
 *
 *   return <Link onMouseEnter={handleMouseEnter}>View Profile</Link>;
 * }
 * ```
 */
export async function prefetchQuery<T>(
  queryKey: unknown[],
  queryFn: () => Promise<T>,
  staleTime?: number
) {
  await queryClient.prefetchQuery({
    queryKey,
    queryFn,
    staleTime,
  });
}

/**
 * Helper function to set query data manually
 *
 * @description Updates cached data without making API call.
 * Useful for optimistic updates or when you already have the data.
 *
 * @param queryKey - The query key to update
 * @param data - The new data to set
 *
 * @example
 * ```typescript
 * // Update user data after successful mutation
 * setQueryData(['user', userId], updatedUser);
 *
 * // Optimistic update before mutation
 * const previousUser = getQueryData(['user', userId]);
 * setQueryData(['user', userId], { ...previousUser, name: 'New Name' });
 * ```
 */
export function setQueryData<T>(queryKey: unknown[], data: T) {
  queryClient.setQueryData(queryKey, data);
}

/**
 * Helper function to get cached query data
 *
 * @description Retrieves data from cache without triggering refetch.
 * Returns undefined if data doesn't exist in cache.
 *
 * @param queryKey - The query key to retrieve
 * @returns The cached data or undefined
 *
 * @example
 * ```typescript
 * const cachedUser = getQueryData(['user', userId]);
 * if (cachedUser) {
 *   console.log('Using cached data:', cachedUser);
 * }
 * ```
 */
export function getQueryData<T>(queryKey: unknown[]): T | undefined {
  return queryClient.getQueryData(queryKey);
}
