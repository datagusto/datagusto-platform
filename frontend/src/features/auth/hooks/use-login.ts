/**
 * Login mutation hook
 *
 * @description Custom hook for user authentication using TanStack Query.
 * Handles login API call, token storage, user data fetching, and navigation.
 *
 * **Features**:
 * - Automatic error handling
 * - Loading states
 * - Success/error callbacks
 * - Integration with Zustand store for token management
 * - Automatic navigation to dashboard on success
 *
 * @module use-login
 */

import { useMutation } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { authService, organizationService } from '../services';
import { useAuthStore } from '../stores';
import type { LoginCredentials } from '../types';

/**
 * Login mutation hook
 *
 * @description React hook for logging in users. Uses TanStack Query's useMutation
 * for optimal state management, error handling, and side effects.
 *
 * **Flow**:
 * 1. User submits login form
 * 2. Call `mutate()` or `mutateAsync()` with credentials
 * 3. authService.login() sends request to backend
 * 4. On success:
 *    - Fetch current user data
 *    - Store token and user in Zustand
 *    - Navigate to /dashboard
 * 5. On error:
 *    - Error is available in mutation state
 *    - Display error message to user
 *
 * **State Management**:
 * - `isPending`: Loading state during login
 * - `isError`: True if login failed
 * - `error`: Error object with details
 * - `isSuccess`: True if login succeeded
 *
 * **Integration with Zustand**:
 * After successful login, user data and tokens are stored in Zustand store
 * for access throughout the application.
 *
 * @returns {UseMutationResult} TanStack Query mutation result
 * @property {Function} mutate - Trigger login (fire-and-forget)
 * @property {Function} mutateAsync - Trigger login (returns Promise)
 * @property {boolean} isPending - True while login is in progress
 * @property {boolean} isError - True if login failed
 * @property {Error | null} error - Error object if login failed
 * @property {boolean} isSuccess - True if login succeeded
 * @property {Function} reset - Reset mutation state
 *
 * @example
 * ```tsx
 * import { useLogin } from '@/features/auth/hooks';
 *
 * function LoginForm() {
 *   const loginMutation = useLogin();
 *   const [email, setEmail] = useState('');
 *   const [password, setPassword] = useState('');
 *
 *   const handleSubmit = (e) => {
 *     e.preventDefault();
 *     loginMutation.mutate({ email, password });
 *   };
 *
 *   return (
 *     <form onSubmit={handleSubmit}>
 *       <input
 *         type="email"
 *         value={email}
 *         onChange={(e) => setEmail(e.target.value)}
 *       />
 *       <input
 *         type="password"
 *         value={password}
 *         onChange={(e) => setPassword(e.target.value)}
 *       />
 *
 *       {loginMutation.isError && (
 *         <div className="error">
 *           {loginMutation.error.message}
 *         </div>
 *       )}
 *
 *       <button
 *         type="submit"
 *         disabled={loginMutation.isPending}
 *       >
 *         {loginMutation.isPending ? 'Logging in...' : 'Login'}
 *       </button>
 *     </form>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // With react-hook-form
 * import { useForm } from 'react-hook-form';
 * import { zodResolver } from '@hookform/resolvers/zod';
 * import { signInSchema, type SignInFormData } from '../schemas';
 *
 * function SignInForm() {
 *   const loginMutation = useLogin();
 *   const { register, handleSubmit } = useForm<SignInFormData>({
 *     resolver: zodResolver(signInSchema),
 *   });
 *
 *   const onSubmit = (data: SignInFormData) => {
 *     loginMutation.mutate(data);
 *   };
 *
 *   return (
 *     <form onSubmit={handleSubmit(onSubmit)}>
 *       <input {...register('email')} />
 *       <input {...register('password')} type="password" />
 *       <button type="submit" disabled={loginMutation.isPending}>
 *         Login
 *       </button>
 *     </form>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // With async/await (custom error handling)
 * async function handleLogin(credentials: LoginCredentials) {
 *   try {
 *     await loginMutation.mutateAsync(credentials);
 *     toast.success('Login successful!');
 *   } catch (error) {
 *     if (error instanceof ApiError) {
 *       if (error.status === 401) {
 *         toast.error('Invalid email or password');
 *       } else if (error.status === 429) {
 *         toast.error('Too many attempts, please try again later');
 *       } else {
 *         toast.error('Login failed, please try again');
 *       }
 *     }
 *   }
 * }
 * ```
 */
export function useLogin() {
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);
  const setCurrentOrganization = useAuthStore(
    (state) => state.setCurrentOrganization
  );

  return useMutation({
    /**
     * Mutation function that calls auth service
     *
     * @param credentials - User login credentials
     * @returns Promise<TokenResponse> - JWT tokens from backend
     */
    mutationFn: (credentials: LoginCredentials) =>
      authService.login(credentials),

    /**
     * Success callback
     *
     * @description Called after successful login.
     * Fetches user data and organizations, then stores them in Zustand along with tokens.
     *
     * **Flow**:
     * 1. Store token temporarily for API calls
     * 2. Fetch user profile via GET /auth/me
     * 3. Fetch user's organizations via GET /auth/me/organizations
     * 4. Store authentication data in Zustand
     * 5. Select organization (auto-select first one for now)
     * 6. Navigate to dashboard
     *
     * **Note**: Organization ID cannot be determined at login time because users
     * can belong to multiple organizations (N:M relationship). Frontend must
     * fetch organizations and select one.
     */
    onSuccess: async (data) => {
      try {
        // Store token temporarily for API calls
        useAuthStore.getState().setToken(data.access_token);

        // Fetch full user profile
        const user = await authService.getCurrentUser();

        // Fetch user's organizations
        const organizations = await organizationService.listMyOrganizations();

        // Store authentication data in Zustand (token + user + refreshToken)
        setAuth(data.access_token, user, data.refresh_token);

        // Select organization based on count
        if (organizations.length === 1) {
          // Single organization: auto-select and go to organization projects page
          setCurrentOrganization(organizations[0].id);
          router.push(`/organizations/${organizations[0].id}`);
        } else if (organizations.length > 1) {
          // Multiple organizations: redirect to selection page
          router.push('/select-organization?from=login');
        } else {
          // User has no organizations (should not happen normally)
          throw new Error('User does not belong to any organization');
        }
      } catch (error) {
        // If fetching user or organizations fails, clear the temporary token
        useAuthStore.getState().clearAuth();

        // Re-throw error to trigger mutation error state
        throw error;
      }
    },

    /**
     * Error callback
     *
     * @description Called when login fails.
     * Errors are automatically handled by TanStack Query and available in mutation.error
     *
     * @note You can add custom error handling here (e.g., logging, analytics)
     */
    onError: () => {
      // Errors are handled in components via mutation.error
    },
  });
}
