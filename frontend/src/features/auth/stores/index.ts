/**
 * Auth stores barrel export
 *
 * @description Centralizes exports for Zustand stores related to authentication.
 * Currently exports the main auth store for client-side state management.
 *
 * @example
 * ```typescript
 * import { useAuthStore, isAuthenticated, getToken } from '@/features/auth/stores';
 * ```
 */

export { useAuthStore, isAuthenticated, getToken, getUser } from './auth.store';
