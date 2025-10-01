/**
 * Sign-in page
 *
 * @description Page for user authentication. Displays sign-in form and handles login flow.
 *
 * @module sign-in-page
 */

import { SignInForm } from '@/features/auth/components';

/**
 * Sign-in page component
 *
 * @description Renders the sign-in page with form and instructions.
 * Form logic is handled by SignInForm component.
 *
 * **Route**: /sign-in
 *
 * **Features**:
 * - Email and password login
 * - Validation and error handling
 * - Link to sign-up page
 * - Automatic redirect to dashboard on success
 *
 * @example
 * ```
 * // User navigates to /sign-in
 * // Sees this page with sign-in form
 * // After successful login, redirected to /dashboard
 * ```
 */
export default function SignInPage() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-12">
      <div className="w-full max-w-md border rounded-md p-6 bg-white">
        <h1 className="text-2xl font-bold mb-2">Sign In</h1>
        <p className="text-sm text-gray-600 mb-6">
          Enter your credentials to access your account
        </p>

        <SignInForm />
      </div>
    </div>
  );
}
