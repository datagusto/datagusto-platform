/**
 * Current user query hook
 *
 * @description Custom hook for fetching current authenticated user data using TanStack Query.
 * Provides automatic caching, background refetching, and loading states.
 *
 * **Features**:
 * - Automatic caching (reduces API calls)
 * - Background refetching on stale data
 * - Loading and error states
 * - Conditional fetching (only when authenticated)
 * - Integration with Zustand store
 *
 * @module use-current-user
 */

import { useQuery } from '@tanstack/react-query';
import { authService } from '../services';
import { useAuthStore } from '../stores';

/**
 * Query key for current user
 *
 * @description Unique identifier for the current user query in TanStack Query cache.
 * Used for:
 * - Caching user data
 * - Invalidating cache after updates
 * - Sharing query state across components
 *
 * @constant
 */
export const CURRENT_USER_QUERY_KEY = ['currentUser'];

/**
 * Current user query hook
 *
 * @description React hook for fetching authenticated user data. Uses TanStack Query's useQuery
 * for optimal caching, automatic background updates, and state management.
 *
 * **Flow**:
 * 1. Check if user has authentication token (from Zustand)
 * 2. If authenticated, fetch user data from API
 * 3. Cache data for 5 minutes (staleTime)
 * 4. Keep in memory for 10 minutes (gcTime)
 * 5. Automatically refetch when data is stale and component re-mounts
 *
 * **Caching Behavior**:
 * - **staleTime**: 5 minutes - Data is considered "fresh" for 5 minutes
 * - **gcTime**: 10 minutes - Unused data stays in memory for 10 minutes
 * - **refetchOnMount**: true - Refetch if data is stale when component mounts
 * - **refetchOnWindowFocus**: false - Don't refetch when window regains focus
 *
 * **Conditional Fetching**:
 * Query only runs when user has authentication token. If not authenticated,
 * query remains idle and doesn't make API calls.
 *
 * **Integration with Zustand**:
 * Token is read from Zustand store to determine if user is authenticated.
 * User data can optionally be cached in Zustand for faster access.
 *
 * @returns {UseQueryResult} TanStack Query result
 * @property {User | undefined} data - User object if authenticated and fetched
 * @property {boolean} isLoading - True on initial load
 * @property {boolean} isFetching - True during any fetch (including background)
 * @property {boolean} isError - True if fetch failed
 * @property {Error | null} error - Error object if fetch failed
 * @property {boolean} isSuccess - True if fetch succeeded
 * @property {Function} refetch - Manually trigger refetch
 *
 * @example
 * ```tsx
 * import { useCurrentUser } from '@/features/auth/hooks';
 *
 * function UserProfile() {
 *   const { data: user, isLoading, isError, error } = useCurrentUser();
 *
 *   if (isLoading) {
 *     return <div>Loading user data...</div>;
 *   }
 *
 *   if (isError) {
 *     return <div>Error: {error.message}</div>;
 *   }
 *
 *   if (!user) {
 *     return <div>Not authenticated</div>;
 *   }
 *
 *   return (
 *     <div>
 *       <h1>Welcome, {user.name}!</h1>
 *       <p>Email: {user.email}</p>
 *       <p>Account active: {user.is_active ? 'Yes' : 'No'}</p>
 *     </div>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Display user avatar in navbar (cached data)
 * function Navbar() {
 *   const { data: user } = useCurrentUser();
 *
 *   return (
 *     <nav>
 *       <div>My App</div>
 *       {user && (
 *         <div>
 *           <img src={user.avatar} alt={user.name} />
 *           <span>{user.name}</span>
 *         </div>
 *       )}
 *     </nav>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Conditionally render content based on user data
 * function Dashboard() {
 *   const { data: user, isLoading } = useCurrentUser();
 *
 *   if (isLoading) return <Spinner />;
 *
 *   return (
 *     <div>
 *       <h1>Dashboard</h1>
 *       {user?.is_active ? (
 *         <ActiveUserContent />
 *       ) : (
 *         <InactiveUserWarning />
 *       )}
 *     </div>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Manually refetch user data (e.g., after profile update)
 * function ProfileEditForm() {
 *   const { data: user, refetch } = useCurrentUser();
 *   const updateMutation = useMutation({
 *     mutationFn: updateProfile,
 *     onSuccess: () => {
 *       refetch(); // Refresh user data
 *       toast.success('Profile updated!');
 *     },
 *   });
 *
 *   return <form onSubmit={handleSubmit}>...</form>;
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Using with query invalidation (preferred method)
 * import { useQueryClient } from '@tanstack/react-query';
 * import { CURRENT_USER_QUERY_KEY } from './use-current-user';
 *
 * function ProfileEditForm() {
 *   const queryClient = useQueryClient();
 *
 *   const updateMutation = useMutation({
 *     mutationFn: updateProfile,
 *     onSuccess: () => {
 *       // Invalidate and refetch
 *       queryClient.invalidateQueries({ queryKey: CURRENT_USER_QUERY_KEY });
 *       toast.success('Profile updated!');
 *     },
 *   });
 *
 *   return <form onSubmit={handleSubmit}>...</form>;
 * }
 * ```
 */
export function useCurrentUser() {
  // Get authentication token from Zustand store
  // Query only runs if token exists (enabled: !!token)
  const token = useAuthStore((state) => state.token);

  return useQuery({
    /**
     * Query key for caching and identification
     *
     * Uses constant CURRENT_USER_QUERY_KEY for consistency.
     * This key is used across the app to invalidate/refetch this query.
     */
    queryKey: CURRENT_USER_QUERY_KEY,

    /**
     * Query function that fetches user data
     *
     * Calls authService.getCurrentUser() which:
     * - Adds Bearer token to Authorization header (from Zustand)
     * - Makes GET request to /api/v1/auth/me
     * - Returns User object
     * - Throws ApiError on failure
     */
    queryFn: () => authService.getCurrentUser(),

    /**
     * Conditional fetching
     *
     * Only fetch user data when:
     * - User has authentication token
     * - Token is stored in Zustand store
     *
     * When enabled is false:
     * - Query doesn't run
     * - No API calls made
     * - data remains undefined
     * - isLoading is false (not true!)
     */
    enabled: !!token,

    /**
     * Stale time
     *
     * How long data is considered "fresh" before becoming "stale".
     * Stale data triggers refetch on:
     * - Component mount
     * - Window refocus (if enabled)
     * - Network reconnection
     *
     * 5 minutes is good balance between:
     * - Reducing unnecessary API calls
     * - Keeping data reasonably up-to-date
     */
    staleTime: 5 * 60 * 1000, // 5 minutes

    /**
     * Garbage collection time (formerly cacheTime)
     *
     * How long unused data stays in memory after all observers unmount.
     * After this time, data is removed from cache.
     *
     * 10 minutes ensures:
     * - Quick page switches don't require refetch
     * - Memory is eventually freed
     */
    gcTime: 10 * 60 * 1000, // 10 minutes

    /**
     * Retry configuration
     *
     * Retry once on failure to handle transient errors.
     * Don't retry on:
     * - 401 Unauthorized (token expired, logout user)
     * - 403 Forbidden (insufficient permissions)
     * - 404 Not Found (user doesn't exist)
     */
    retry: (failureCount, error: unknown) => {
      // Don't retry on authentication errors
      if (
        error &&
        typeof error === 'object' &&
        'status' in error &&
        (error.status === 401 || error.status === 403)
      ) {
        return false;
      }
      // Retry once for other errors
      return failureCount < 1;
    },

    /**
     * Refetch on mount
     *
     * Refetch stale data when component mounts.
     * Ensures data is fresh when user navigates to page.
     */
    refetchOnMount: true,

    /**
     * Refetch on window focus
     *
     * Disabled to reduce API calls.
     * User data doesn't change frequently enough to justify refetching
     * every time window regains focus.
     */
    refetchOnWindowFocus: false,

    /**
     * Refetch on reconnect
     *
     * Refetch data when network connection is restored.
     * Ensures data is up-to-date after offline period.
     */
    refetchOnReconnect: true,
  });
}
