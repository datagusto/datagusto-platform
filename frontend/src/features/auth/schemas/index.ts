/**
 * Auth schemas barrel export
 *
 * @description Centralizes exports for Zod validation schemas used in authentication.
 * Schemas provide type-safe validation for forms and API data.
 *
 * @example
 * ```typescript
 * import { signInSchema, signUpSchema, type SignInFormData } from '@/features/auth/schemas';
 * ```
 */

export { signInSchema, signUpSchema, registerDataSchema } from './auth.schema';

export type {
  SignInFormData,
  SignUpFormData,
  RegisterData,
} from './auth.schema';
