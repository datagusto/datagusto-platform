/**
 * Authentication store using Zustand
 *
 * @description Manages client-side authentication state including tokens and user data.
 * Uses Zustand with middleware for:
 * - **persist**: Automatically syncs state to localStorage for persistence across sessions
 * - **devtools**: Integrates with Redux DevTools for debugging state changes
 *
 * **Architecture Decision**:
 * This store manages CLIENT state (tokens, basic auth flags). User data from the server
 * is managed by TanStack Query for optimal caching and synchronization.
 *
 * @module auth.store
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { User } from '../types';

/**
 * Authentication state interface
 *
 * @interface AuthState
 * @property {string | null} token - JWT access token for API authentication
 * @property {string | null} refreshToken - JWT refresh token for obtaining new access tokens
 * @property {User | null} user - Currently authenticated user (cached from TanStack Query)
 * @property {function} setAuth - Updates authentication state with new tokens and user
 * @property {function} setToken - Updates only the access token (used after refresh)
 * @property {function} clearAuth - Clears all authentication state (logout)
 */
interface AuthState {
  /** JWT access token - included in Authorization header for API requests */
  token: string | null;

  /** JWT refresh token - used to obtain new access tokens when they expire */
  refreshToken: string | null;

  /** Cached user data (also managed by TanStack Query for freshness) */
  user: User | null;

  /** Currently selected organization ID (included in X-Organization-ID header) */
  currentOrganizationId: string | null;

  /** Whether the store has been hydrated from localStorage */
  _hasHydrated: boolean;

  /** Internal method to mark hydration as complete */
  _setHasHydrated: (state: boolean) => void;

  /**
   * Sets authentication state after successful login
   *
   * @param token - JWT access token
   * @param user - Authenticated user data
   * @param refreshToken - Optional JWT refresh token
   *
   * @example
   * ```typescript
   * const setAuth = useAuthStore((state) => state.setAuth);
   * setAuth('eyJhbGc...', { id: '1', email: 'user@example.com', ... }, 'refresh_token');
   * ```
   */
  setAuth: (token: string, user: User, refreshToken?: string) => void;

  /**
   * Updates only the access token
   *
   * @description Used when refreshing access token without re-fetching user data
   * @param token - New JWT access token
   *
   * @example
   * ```typescript
   * const setToken = useAuthStore((state) => state.setToken);
   * setToken('new_access_token');
   * ```
   */
  setToken: (token: string) => void;

  /**
   * Sets the currently selected organization
   *
   * @description Updates the current organization ID for X-Organization-ID header.
   * @param organizationId - Organization UUID to switch to
   *
   * @example
   * ```typescript
   * const setCurrentOrganization = useAuthStore((state) => state.setCurrentOrganization);
   * setCurrentOrganization('456e7890-e12b-34c5-a678-123456789000');
   * ```
   */
  setCurrentOrganization: (organizationId: string) => void;

  /**
   * Clears all authentication state
   *
   * @description Removes token, refreshToken, user, and currentOrganizationId from state and localStorage.
   * Call this function during logout.
   *
   * @example
   * ```typescript
   * const clearAuth = useAuthStore((state) => state.clearAuth);
   * clearAuth(); // Logs out user
   * ```
   */
  clearAuth: () => void;
}

/**
 * Auth store instance
 *
 * @description Global Zustand store for authentication state. Configured with:
 * - **persist middleware**: Syncs to localStorage under 'auth-storage' key
 * - **devtools middleware**: Enables Redux DevTools with name 'AuthStore'
 *
 * **Performance Note**:
 * Use selective subscriptions to prevent unnecessary re-renders:
 * ```typescript
 * // ✅ Good: Only re-renders when token changes
 * const token = useAuthStore((state) => state.token);
 *
 * // ❌ Bad: Re-renders on any state change
 * const store = useAuthStore();
 * ```
 *
 * **Middleware Order**:
 * devtools(persist(...)) ensures persistence happens before devtools logging
 *
 * @example
 * ```typescript
 * // In a component - get token
 * function ApiClient() {
 *   const token = useAuthStore((state) => state.token);
 *   return <div>Token: {token}</div>;
 * }
 * ```
 *
 * @example
 * ```typescript
 * // In a component - login
 * function LoginButton() {
 *   const setAuth = useAuthStore((state) => state.setAuth);
 *
 *   const handleLogin = async () => {
 *     const { token, user } = await loginApi();
 *     setAuth(token, user);
 *   };
 *
 *   return <button onClick={handleLogin}>Login</button>;
 * }
 * ```
 *
 * @example
 * ```typescript
 * // Outside React components - get token
 * import { useAuthStore } from '@/features/auth/stores';
 *
 * async function apiCall() {
 *   const token = useAuthStore.getState().token;
 *   const response = await fetch('/api/data', {
 *     headers: { Authorization: `Bearer ${token}` }
 *   });
 * }
 * ```
 *
 * @example
 * ```typescript
 * // Logout
 * function LogoutButton() {
 *   const clearAuth = useAuthStore((state) => state.clearAuth);
 *   return <button onClick={clearAuth}>Logout</button>;
 * }
 * ```
 */
export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set) => ({
        // Initial state
        token: null,
        refreshToken: null,
        user: null,
        currentOrganizationId: null,
        _hasHydrated: false,

        // Actions
        _setHasHydrated: (state) => {
          set({ _hasHydrated: state });
        },

        setAuth: (token, user, refreshToken) =>
          set(
            {
              token,
              user,
              refreshToken: refreshToken ?? null,
            },
            false,
            'auth/setAuth' // Action name for Redux DevTools
          ),

        setToken: (token) =>
          set(
            { token },
            false,
            'auth/setToken' // Action name for Redux DevTools
          ),

        setCurrentOrganization: (organizationId) =>
          set(
            { currentOrganizationId: organizationId },
            false,
            'auth/setCurrentOrganization' // Action name for Redux DevTools
          ),

        clearAuth: () =>
          set(
            {
              token: null,
              refreshToken: null,
              user: null,
              currentOrganizationId: null,
            },
            false,
            'auth/clearAuth' // Action name for Redux DevTools
          ),
      }),
      {
        name: 'auth-storage', // localStorage key name
        // Optional: Customize which parts of state to persist
        // partialize: (state) => ({ token: state.token, refreshToken: state.refreshToken }),
        onRehydrateStorage: () => (state) => {
          state?._setHasHydrated(true);
        },
      }
    ),
    {
      name: 'AuthStore', // Name shown in Redux DevTools
      enabled: process.env.NODE_ENV === 'development', // Only enable in development
    }
  )
);

/**
 * Helper function to check if user is authenticated
 *
 * @description Convenience function to check authentication status without subscribing to store.
 * Useful for one-time checks or outside React components.
 *
 * @returns {boolean} True if user has a valid token, false otherwise
 *
 * @example
 * ```typescript
 * if (isAuthenticated()) {
 *   console.log('User is logged in');
 * } else {
 *   console.log('User is not logged in');
 * }
 * ```
 */
export function isAuthenticated(): boolean {
  return !!useAuthStore.getState().token;
}

/**
 * Helper function to get current token
 *
 * @description Convenience function to get token without subscribing to store.
 * Useful for API clients and middleware.
 *
 * @returns {string | null} Current access token or null if not authenticated
 *
 * @example
 * ```typescript
 * const token = getToken();
 * if (token) {
 *   fetch('/api/data', {
 *     headers: { Authorization: `Bearer ${token}` }
 *   });
 * }
 * ```
 */
export function getToken(): string | null {
  return useAuthStore.getState().token;
}

/**
 * Helper function to get current user
 *
 * @description Convenience function to get user without subscribing to store.
 * Note: For up-to-date user data, prefer using TanStack Query's useCurrentUser hook.
 *
 * @returns {User | null} Current user or null if not authenticated
 *
 * @example
 * ```typescript
 * const user = getUser();
 * console.log(user?.email);
 * ```
 */
export function getUser(): User | null {
  return useAuthStore.getState().user;
}
