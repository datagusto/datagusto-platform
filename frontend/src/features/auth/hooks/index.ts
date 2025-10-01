/**
 * Auth hooks barrel export
 *
 * @description Centralizes exports for all authentication-related hooks.
 * These hooks integrate with TanStack Query for server state management.
 *
 * @example
 * ```typescript
 * import { useAuth, useLogin, useRegister, useSwitchOrganization } from '@/features/auth/hooks';
 * ```
 */

export { useAuth } from './use-auth';
export { useLogin } from './use-login';
export { useRegister } from './use-register';
export { useCurrentUser, CURRENT_USER_QUERY_KEY } from './use-current-user';
export { useSwitchOrganization } from './use-switch-organization';

export type { UseAuthResult } from './use-auth';
