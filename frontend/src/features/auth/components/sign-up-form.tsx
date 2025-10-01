/**
 * Sign-up form component
 *
 * @description Form component for new user registration with name, email, and password.
 * Includes password confirmation, validation, error handling, and loading states.
 *
 * **Features**:
 * - Name, email, password, and password confirmation fields
 * - Validation with Zod (including password match check)
 * - react-hook-form for form state management
 * - TanStack Query for registration mutation
 * - Error message display
 * - Loading state during submission
 * - Link to sign-in page
 *
 * @module sign-up-form
 */

'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import Link from 'next/link';
import { useRegister } from '../hooks';
import { signUpSchema, type SignUpFormData } from '../schemas';

/**
 * Sign-up form component
 *
 * @description Renders a registration form with name, email, password, and password confirmation.
 * Handles validation, submission, and error display.
 *
 * **Form Fields**:
 * - Name: Minimum 2 characters
 * - Email: Validated as email format
 * - Password: Minimum 8 characters
 * - Confirm Password: Must match password
 *
 * **Validation**:
 * - Client-side validation with Zod schema
 * - Password confirmation check
 * - Real-time error messages
 * - Submit button disabled during submission
 *
 * **Error Handling**:
 * - Validation errors displayed under fields
 * - API errors displayed at top of form
 * - Specific error messages for duplicate email, etc.
 *
 * **Flow**:
 * 1. User enters registration data
 * 2. Client-side validation on blur/submit
 * 3. On submit, call register mutation (excludes confirmPassword)
 * 4. On success, redirect to sign-in (handled by useRegister)
 * 5. On error, display error message
 *
 * @example
 * ```tsx
 * // In a page component
 * import { SignUpForm } from '@/features/auth/components';
 *
 * export default function SignUpPage() {
 *   return (
 *     <div>
 *       <h1>Create an Account</h1>
 *       <SignUpForm />
 *     </div>
 *   );
 * }
 * ```
 */
export function SignUpForm() {
  // Registration mutation from TanStack Query
  const registerMutation = useRegister();

  // Form state management with react-hook-form
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SignUpFormData>({
    resolver: zodResolver(signUpSchema),
    defaultValues: {
      name: '',
      email: '',
      password: '',
      confirmPassword: '',
    },
  });

  /**
   * Form submission handler
   *
   * @description Excludes confirmPassword before sending to API.
   * confirmPassword is only for client-side validation.
   *
   * @param data - Validated form data
   */
  const onSubmit = (data: SignUpFormData) => {
    // Remove confirmPassword before submitting to API
    const { confirmPassword: _confirmPassword, ...registrationData } = data;
    registerMutation.mutate(registrationData);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* API Error Display */}
      {registerMutation.isError && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">
          {registerMutation.error?.message || 'Failed to register'}
        </div>
      )}

      {/* Name Field */}
      <div>
        <label htmlFor="name" className="block text-sm font-medium mb-1">
          Full Name
        </label>
        <input
          id="name"
          type="text"
          className="w-full border rounded-md px-3 py-2"
          placeholder="John Doe"
          {...register('name')}
        />
        {errors.name && (
          <p className="mt-1 text-xs text-red-600">{errors.name.message}</p>
        )}
      </div>

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

      {/* Confirm Password Field */}
      <div>
        <label
          htmlFor="confirmPassword"
          className="block text-sm font-medium mb-1"
        >
          Confirm Password
        </label>
        <input
          id="confirmPassword"
          type="password"
          className="w-full border rounded-md px-3 py-2"
          placeholder="••••••••"
          {...register('confirmPassword')}
        />
        {errors.confirmPassword && (
          <p className="mt-1 text-xs text-red-600">
            {errors.confirmPassword.message}
          </p>
        )}
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isSubmitting || registerMutation.isPending}
        className="w-full bg-black text-white rounded-md py-2 disabled:opacity-60"
      >
        {registerMutation.isPending ? 'Creating Account...' : 'Create Account'}
      </button>

      {/* Sign-in Link */}
      <p className="text-sm text-gray-500 text-center mt-6">
        Already have an account?{' '}
        <Link href="/sign-in" className="font-medium underline">
          Sign in
        </Link>
      </p>
    </form>
  );
}
