/**
 * Sign-in form component
 *
 * @description Form component for user authentication with email and password.
 * Includes validation, error handling, and loading states.
 *
 * **Features**:
 * - Email and password validation with Zod
 * - react-hook-form for form state management
 * - TanStack Query for login mutation
 * - Error message display
 * - Loading state during submission
 * - Link to sign-up page
 *
 * @module sign-in-form
 */

'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import Link from 'next/link';
import { useLogin } from '../hooks';
import { signInSchema, type SignInFormData } from '../schemas';

/**
 * Sign-in form component
 *
 * @description Renders a login form with email and password fields.
 * Handles validation, submission, and error display.
 *
 * **Form Fields**:
 * - Email: Validated as email format
 * - Password: Minimum 8 characters
 *
 * **Validation**:
 * - Client-side validation with Zod schema
 * - Real-time error messages
 * - Submit button disabled during submission
 *
 * **Error Handling**:
 * - Validation errors displayed under fields
 * - API errors displayed at top of form
 * - User-friendly error messages
 *
 * **Flow**:
 * 1. User enters email and password
 * 2. Client-side validation on blur/submit
 * 3. On submit, call login mutation
 * 4. On success, redirect to dashboard (handled by useLogin)
 * 5. On error, display error message
 *
 * @example
 * ```tsx
 * // In a page component
 * import { SignInForm } from '@/features/auth/components';
 *
 * export default function SignInPage() {
 *   return (
 *     <div>
 *       <h1>Sign In</h1>
 *       <SignInForm />
 *     </div>
 *   );
 * }
 * ```
 */
export function SignInForm() {
  // Login mutation from TanStack Query
  const loginMutation = useLogin();

  // Form state management with react-hook-form
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SignInFormData>({
    resolver: zodResolver(signInSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  /**
   * Form submission handler
   *
   * @param data - Validated form data
   */
  const onSubmit = (data: SignInFormData) => {
    loginMutation.mutate(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* API Error Display */}
      {loginMutation.isError && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">
          {loginMutation.error?.message || 'Failed to sign in'}
        </div>
      )}

      {/* Email Field */}
      <div>
        <label htmlFor="email" className="block text-sm font-medium mb-1">
          Email
        </label>
        <input
          id="email"
          type="email"
          className="w-full border rounded-md px-3 py-2"
          placeholder="your.email@example.com"
          {...register('email')}
        />
        {errors.email && (
          <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>
        )}
      </div>

      {/* Password Field */}
      <div>
        <label htmlFor="password" className="block text-sm font-medium mb-1">
          Password
        </label>
        <input
          id="password"
          type="password"
          className="w-full border rounded-md px-3 py-2"
          placeholder="••••••••"
          {...register('password')}
        />
        {errors.password && (
          <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>
        )}
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isSubmitting || loginMutation.isPending}
        className="w-full bg-black text-white rounded-md py-2 disabled:opacity-60"
      >
        {loginMutation.isPending ? 'Signing in...' : 'Sign In'}
      </button>

      {/* Sign-up Link */}
      <p className="text-sm text-gray-500 text-center mt-6">
        Don&apos;t have an account?{' '}
        <Link href="/sign-up" className="font-medium underline">
          Sign up
        </Link>
      </p>
    </form>
  );
}
