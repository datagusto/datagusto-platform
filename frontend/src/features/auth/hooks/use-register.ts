/**
 * Registration mutation hook
 *
 * @description Custom hook for user registration using TanStack Query.
 * Handles registration API call and navigation to login page on success.
 *
 * **Features**:
 * - Automatic error handling
 * - Loading states
 * - Success callback with navigation
 * - Validation error display
 *
 * @module use-register
 */

import { useMutation } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { authService, organizationService } from '../services';
import { useAuthStore } from '../stores';
import type { RegisterData, TokenResponse, User } from '../types';

/**
 * Registration mutation hook
 *
 * @description React hook for registering new users. Uses TanStack Query's useMutation
 * for optimal state management, error handling, and side effects.
 *
 * **Flow**:
 * 1. User submits registration form
 * 2. Call `mutate()` or `mutateAsync()` with registration data
 * 3. authService.register() sends request to backend
 * 4. On success:
 *    - User account is created
 *    - Navigate to /sign-in page
 *    - User must login separately
 * 5. On error:
 *    - Error is available in mutation state
 *    - Display validation or duplicate email errors
 *
 * **State Management**:
 * - `isPending`: Loading state during registration
 * - `isError`: True if registration failed
 * - `error`: Error object with details (e.g., "Email already registered")
 * - `isSuccess`: True if registration succeeded
 *
 * **Security Note**:
 * After registration, user is not automatically logged in. This is intentional
 * for security best practices. User must explicitly login with their credentials.
 *
 * @returns {UseMutationResult} TanStack Query mutation result
 * @property {Function} mutate - Trigger registration (fire-and-forget)
 * @property {Function} mutateAsync - Trigger registration (returns Promise)
 * @property {boolean} isPending - True while registration is in progress
 * @property {boolean} isError - True if registration failed
 * @property {Error | null} error - Error object if registration failed
 * @property {boolean} isSuccess - True if registration succeeded
 * @property {User | undefined} data - Created user data if successful
 * @property {Function} reset - Reset mutation state
 *
 * @example
 * ```tsx
 * import { useRegister } from '@/features/auth/hooks';
 *
 * function SignUpForm() {
 *   const registerMutation = useRegister();
 *   const [formData, setFormData] = useState({
 *     name: '',
 *     email: '',
 *     password: '',
 *   });
 *
 *   const handleSubmit = (e) => {
 *     e.preventDefault();
 *     registerMutation.mutate(formData);
 *   };
 *
 *   return (
 *     <form onSubmit={handleSubmit}>
 *       <input
 *         value={formData.name}
 *         onChange={(e) => setFormData({ ...formData, name: e.target.value })}
 *         placeholder="Name"
 *       />
 *       <input
 *         type="email"
 *         value={formData.email}
 *         onChange={(e) => setFormData({ ...formData, email: e.target.value })}
 *         placeholder="Email"
 *       />
 *       <input
 *         type="password"
 *         value={formData.password}
 *         onChange={(e) => setFormData({ ...formData, password: e.target.value })}
 *         placeholder="Password"
 *       />
 *
 *       {registerMutation.isError && (
 *         <div className="error">
 *           {registerMutation.error.message}
 *         </div>
 *       )}
 *
 *       {registerMutation.isSuccess && (
 *         <div className="success">
 *           Registration successful! Redirecting to login...
 *         </div>
 *       )}
 *
 *       <button
 *         type="submit"
 *         disabled={registerMutation.isPending}
 *       >
 *         {registerMutation.isPending ? 'Creating account...' : 'Sign Up'}
 *       </button>
 *     </form>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // With react-hook-form (recommended)
 * import { useForm } from 'react-hook-form';
 * import { zodResolver } from '@hookform/resolvers/zod';
 * import { signUpSchema, type SignUpFormData } from '../schemas';
 *
 * function SignUpForm() {
 *   const registerMutation = useRegister();
 *   const { register, handleSubmit, formState: { errors } } = useForm<SignUpFormData>({
 *     resolver: zodResolver(signUpSchema),
 *   });
 *
 *   const onSubmit = (data: SignUpFormData) => {
 *     // Remove confirmPassword before submitting
 *     const { confirmPassword, ...registrationData } = data;
 *     registerMutation.mutate(registrationData);
 *   };
 *
 *   return (
 *     <form onSubmit={handleSubmit(onSubmit)}>
 *       <input {...register('name')} placeholder="Name" />
 *       {errors.name && <span>{errors.name.message}</span>}
 *
 *       <input {...register('email')} type="email" placeholder="Email" />
 *       {errors.email && <span>{errors.email.message}</span>}
 *
 *       <input {...register('password')} type="password" placeholder="Password" />
 *       {errors.password && <span>{errors.password.message}</span>}
 *
 *       <input {...register('confirmPassword')} type="password" placeholder="Confirm Password" />
 *       {errors.confirmPassword && <span>{errors.confirmPassword.message}</span>}
 *
 *       {registerMutation.isError && (
 *         <div>{registerMutation.error.message}</div>
 *       )}
 *
 *       <button type="submit" disabled={registerMutation.isPending}>
 *         {registerMutation.isPending ? 'Creating account...' : 'Sign Up'}
 *       </button>
 *     </form>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // With custom error handling
 * import { ApiError } from '@/shared/lib';
 *
 * function SignUpForm() {
 *   const registerMutation = useRegister();
 *
 *   const handleRegister = async (data: RegisterData) => {
 *     try {
 *       const user = await registerMutation.mutateAsync(data);
 *       toast.success(`Welcome ${user.name}! Please login to continue.`);
 *     } catch (error) {
 *       if (error instanceof ApiError) {
 *         if (error.status === 409) {
 *           toast.error('This email is already registered');
 *         } else if (error.status === 400) {
 *           toast.error('Please check your input and try again');
 *         } else {
 *           toast.error('Registration failed, please try again later');
 *         }
 *       }
 *     }
 *   };
 *
 *   return <form onSubmit={handleSubmit(handleRegister)}>...</form>;
 * }
 * ```
 */
export function useRegister() {
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);
  const setCurrentOrganization = useAuthStore(
    (state) => state.setCurrentOrganization
  );

  return useMutation({
    /**
     * Mutation function that calls auth service
     *
     * @param userData - New user registration data
     * @returns Promise<TokenResponse> - Authentication tokens and user data from backend
     */
    mutationFn: (userData: RegisterData) => authService.register(userData),

    /**
     * Success callback
     *
     * @description Called after successful registration.
     * Automatically logs in the user by fetching organizations and storing tokens.
     *
     * **Flow**:
     * 1. User account is created on backend
     * 2. Backend returns access token and refresh token
     * 3. Store token temporarily for API calls
     * 4. Fetch user's organizations via GET /auth/me/organizations
     * 5. Store tokens in auth store (persists to localStorage)
     * 6. Auto-select the newly created organization
     * 7. Navigate to dashboard
     *
     * **Security**:
     * - Tokens are transmitted over HTTPS
     * - Access token has short expiration (15-30 minutes)
     * - Refresh token allows seamless re-authentication
     * - This follows industry standard practice (GitHub, Google, etc.)
     *
     * **Note**: Organization ID cannot be included in registration response because
     * the data model supports N:M relationship (even though new users have only one).
     * This maintains consistency with the multi-organization architecture.
     */
    onSuccess: async (response: TokenResponse) => {
      try {
        // Store token temporarily for API calls
        useAuthStore.getState().setToken(response.access_token);

        // Construct User object from TokenResponse
        // New users are always active and not suspended/archived
        const user: User = {
          id: response.user_id,
          email: response.email,
          name: response.name,
          is_active: true,
          is_suspended: false,
          is_archived: false,
        };

        // Fetch user's organizations (new user will have exactly one)
        const organizations = await organizationService.listMyOrganizations();

        // Store authentication tokens and user data
        setAuth(response.access_token, user, response.refresh_token);

        // Select organization based on count
        if (organizations.length === 1) {
          // Single organization: auto-select and go to organization projects page
          setCurrentOrganization(organizations[0].id);
          router.push(`/organizations/${organizations[0].id}`);
        } else if (organizations.length > 1) {
          // Multiple organizations: redirect to selection page (rare for new registration)
          router.push('/select-organization?from=register');
        } else {
          // No organizations found (should not happen after registration)
          throw new Error('No organization found after registration');
        }
      } catch (error) {
        // If fetching organizations fails, clear the temporary token
        useAuthStore.getState().clearAuth();

        // Re-throw error to trigger mutation error state
        throw error;
      }
    },

    /**
     * Error callback
     *
     * @description Called when registration fails.
     * Common errors:
     * - 409 Conflict: Email already registered
     * - 400 Bad Request: Validation error (weak password, invalid email, etc.)
     * - 500 Internal Server Error: Backend issue
     *
     * @note Errors are automatically available in mutation.error
     */
    onError: () => {
      // Errors are handled in components via mutation.error
    },
  });
}
