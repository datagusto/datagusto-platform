/**
 * Unified auth hook
 *
 * @description Main authentication hook that combines login, registration, and user data.
 * Provides a unified interface for all authentication operations in the application.
 *
 * **Features**:
 * - Login mutation (with TanStack Query)
 * - Registration mutation (with TanStack Query)
 * - Current user query (with caching)
 * - Logout function
 * - Authentication status
 * - Loading states
 *
 * @module use-auth
 */

import { useCurrentUser } from './use-current-user';
import { useLogin } from './use-login';
import { useRegister } from './use-register';
import { authService } from '../services';

/**
 * Unified auth hook result
 *
 * @interface UseAuthResult
 * @description Combined result from all auth hooks and operations.
 */
export interface UseAuthResult {
  /** Current authenticated user (undefined if not authenticated or loading) */
  user: ReturnType<typeof useCurrentUser>['data'];

  /** True while fetching user data for the first time */
  isLoading: boolean;

  /** True if user is authenticated (has valid token and user data) */
  isAuthenticated: boolean;

  /** Login mutation function (fire-and-forget) */
  login: ReturnType<typeof useLogin>['mutate'];

  /** Async login function (returns Promise) */
  loginAsync: ReturnType<typeof useLogin>['mutateAsync'];

  /** True while login is in progress */
  isLoggingIn: boolean;

  /** Login error (if any) */
  loginError: ReturnType<typeof useLogin>['error'];

  /** Register mutation function (fire-and-forget) */
  register: ReturnType<typeof useRegister>['mutate'];

  /** Async register function (returns Promise) */
  registerAsync: ReturnType<typeof useRegister>['mutateAsync'];

  /** True while registration is in progress */
  isRegistering: boolean;

  /** Registration error (if any) */
  registerError: ReturnType<typeof useRegister>['error'];

  /** Logout function (clears auth state) */
  logout: () => void;

  /** Refetch current user data */
  refetchUser: ReturnType<typeof useCurrentUser>['refetch'];
}

/**
 * Unified authentication hook
 *
 * @description Main hook for all authentication operations. Combines login, registration,
 * user data fetching, and logout into a single convenient interface.
 *
 * **Usage Pattern**:
 * Use this hook as the primary interface for authentication in components.
 * It delegates to specialized hooks internally but provides a clean API.
 *
 * **State Management**:
 * - User data: Managed by TanStack Query (cached, auto-refetched)
 * - Tokens: Managed by Zustand store (persisted to localStorage)
 * - Loading states: Provided by TanStack Query mutations
 *
 * **Benefits**:
 * - Single import for all auth operations
 * - Consistent API across components
 * - Automatic state synchronization
 * - Built-in loading and error states
 *
 * @returns {UseAuthResult} Combined auth state and operations
 *
 * @example
 * ```tsx
 * import { useAuth } from '@/features/auth/hooks';
 *
 * function AuthStatus() {
 *   const { user, isLoading, isAuthenticated, logout } = useAuth();
 *
 *   if (isLoading) {
 *     return <div>Loading...</div>;
 *   }
 *
 *   if (!isAuthenticated) {
 *     return <div>Not logged in</div>;
 *   }
 *
 *   return (
 *     <div>
 *       <p>Welcome, {user.name}!</p>
 *       <button onClick={logout}>Logout</button>
 *     </div>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Login form
 * function LoginForm() {
 *   const { login, isLoggingIn, loginError } = useAuth();
 *   const [email, setEmail] = useState('');
 *   const [password, setPassword] = useState('');
 *
 *   const handleSubmit = (e) => {
 *     e.preventDefault();
 *     login({ email, password });
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
 *       {loginError && <div>{loginError.message}</div>}
 *
 *       <button type="submit" disabled={isLoggingIn}>
 *         {isLoggingIn ? 'Logging in...' : 'Login'}
 *       </button>
 *     </form>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Registration form
 * function SignUpForm() {
 *   const { register, isRegistering, registerError } = useAuth();
 *
 *   const handleSubmit = (data) => {
 *     register(data);
 *   };
 *
 *   return (
 *     <form onSubmit={handleSubmit}>
 *       {registerError && <div>{registerError.message}</div>}
 *       <button type="submit" disabled={isRegistering}>
 *         {isRegistering ? 'Creating account...' : 'Sign Up'}
 *       </button>
 *     </form>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Protected component with auth check
 * function ProtectedComponent() {
 *   const { isAuthenticated, isLoading, user } = useAuth();
 *   const router = useRouter();
 *
 *   useEffect(() => {
 *     if (!isLoading && !isAuthenticated) {
 *       router.push('/sign-in');
 *     }
 *   }, [isAuthenticated, isLoading, router]);
 *
 *   if (isLoading) return <Spinner />;
 *   if (!isAuthenticated) return null;
 *
 *   return <div>Protected content for {user.name}</div>;
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Async operations with error handling
 * function LoginButton() {
 *   const { loginAsync } = useAuth();
 *
 *   const handleLogin = async (credentials) => {
 *     try {
 *       await loginAsync(credentials);
 *       toast.success('Login successful!');
 *     } catch (error) {
 *       toast.error('Login failed: ' + error.message);
 *     }
 *   };
 *
 *   return <button onClick={() => handleLogin(creds)}>Login</button>;
 * }
 * ```
 */
export function useAuth(): UseAuthResult {
  // Fetch current user data (TanStack Query)
  const { data: user, isLoading, refetch: refetchUser } = useCurrentUser();

  // Login mutation
  const loginMutation = useLogin();

  // Registration mutation
  const registerMutation = useRegister();

  // Determine if user is authenticated
  // User is authenticated if user data exists (and token exists implicitly)
  const isAuthenticated = !!user;

  return {
    // User data
    user,
    isLoading,
    isAuthenticated,

    // Login operations
    login: loginMutation.mutate,
    loginAsync: loginMutation.mutateAsync,
    isLoggingIn: loginMutation.isPending,
    loginError: loginMutation.error,

    // Registration operations
    register: registerMutation.mutate,
    registerAsync: registerMutation.mutateAsync,
    isRegistering: registerMutation.isPending,
    registerError: registerMutation.error,

    // Logout operation
    logout: authService.logout,

    // Manual refetch
    refetchUser,
  };
}
