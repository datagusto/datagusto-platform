/**
 * Auth types barrel export
 *
 * @description Centralizes exports for TypeScript type definitions related to authentication.
 * Includes types for User, LoginCredentials, RegisterData, TokenResponse, etc.
 *
 * @example
 * ```typescript
 * import type { User, LoginCredentials, TokenResponse } from '@/features/auth/types';
 * ```
 */

export type {
  User,
  LoginCredentials,
  RegisterData,
  TokenResponse,
  ApiError,
} from './auth.types';
