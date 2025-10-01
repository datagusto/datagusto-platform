/**
 * Sign-up page
 *
 * @description Page for new user registration. Displays sign-up form and handles registration flow.
 *
 * @module sign-up-page
 */

import { SignUpForm } from '@/features/auth/components';

/**
 * Sign-up page component
 *
 * @description Renders the sign-up page with form and instructions.
 * Form logic is handled by SignUpForm component.
 *
 * **Route**: /sign-up
 *
 * **Features**:
 * - New user registration with name, email, password
 * - Password confirmation
 * - Validation and error handling
 * - Link to sign-in page
 * - Automatic redirect to sign-in on success
 *
 * @example
 * ```
 * // User navigates to /sign-up
 * // Sees this page with sign-up form
 * // After successful registration, redirected to /sign-in to login
 * ```
 */
export default function SignUpPage() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-12">
      <div className="w-full max-w-md border rounded-md p-6 bg-white">
        <h1 className="text-2xl font-bold mb-2">Create an Account</h1>
        <p className="text-sm text-gray-600 mb-6">
          Enter your details to create a new account
        </p>

        <SignUpForm />
      </div>
    </div>
  );
}
