# Authentication Feature

## Overview

The authentication feature provides user sign-in, sign-up, and session management functionality. It uses JWT tokens for authentication and integrates with TanStack Query for server state management and Zustand for client state management.

## Architecture

### Directory Structure

```
features/auth/
├── components/           # UI components
│   ├── sign-in-form.tsx
│   ├── sign-up-form.tsx
│   └── index.ts
├── hooks/               # React hooks
│   ├── use-login.ts
│   ├── use-register.ts
│   ├── use-current-user.ts
│   ├── use-auth.ts
│   └── index.ts
├── schemas/             # Zod validation schemas
│   ├── auth.schema.ts
│   └── index.ts
├── services/            # API services
│   ├── auth.service.ts
│   └── index.ts
├── stores/              # Zustand stores
│   ├── auth.store.ts
│   └── index.ts
├── types/               # TypeScript types
│   ├── auth.types.ts
│   └── index.ts
└── README.md            # This file
```

## Core Components

### 1. Authentication Store (Zustand)

**File**: `stores/auth.store.ts`

Manages client-side authentication state using Zustand with persistence and devtools.

**State**:

- `token`: JWT access token
- `refreshToken`: JWT refresh token
- `user`: Current user object

**Actions**:

- `setAuth(token, user, refreshToken?)`: Set authentication state
- `setToken(token)`: Update only the access token
- `clearAuth()`: Clear all authentication data

**Storage**: Persists to localStorage under `auth-storage` key

**Example**:

```typescript
import { useAuthStore } from '@/features/auth/stores';

function MyComponent() {
  const token = useAuthStore((state) => state.token);
  const clearAuth = useAuthStore((state) => state.clearAuth);

  // Access or modify auth state
}
```

### 2. Authentication Service

**File**: `services/auth.service.ts`

Provides API communication methods for authentication operations.

**Methods**:

#### `login(credentials: LoginCredentials): Promise<TokenResponse>`

Authenticates user with email and password. Uses OAuth2 form-urlencoded format.

**Example**:

```typescript
const response = await authService.login({
  email: 'user@example.com',
  password: 'password123',
});
// Returns: { access_token, refresh_token, token_type }
```

#### `register(userData: RegisterData): Promise<User>`

Registers a new user account.

**Example**:

```typescript
const user = await authService.register({
  name: 'John Doe',
  email: 'john@example.com',
  password: 'password123',
});
```

#### `getCurrentUser(): Promise<User>`

Fetches the currently authenticated user's information.

#### `refreshToken(refreshToken: string): Promise<TokenResponse>`

Refreshes an expired access token.

#### `logout(): Promise<void>`

Logs out the current user and clears auth state.

### 3. Authentication Hooks

#### `useLogin()`

**File**: `hooks/use-login.ts`

TanStack Query mutation hook for user login.

**Returns**:

- `mutate(credentials)`: Trigger login
- `mutateAsync(credentials)`: Trigger login (async)
- `isPending`: Loading state
- `isError`: Error state
- `error`: Error object

**Behavior**:

- On success: Stores token, fetches user data, redirects to `/dashboard`
- On error: Error can be accessed via mutation state

**Example**:

```typescript
function SignInForm() {
  const loginMutation = useLogin();

  const handleSubmit = (data) => {
    loginMutation.mutate({
      email: data.email,
      password: data.password
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
      {loginMutation.isPending && <Spinner />}
      {loginMutation.isError && <ErrorMessage error={loginMutation.error} />}
    </form>
  );
}
```

#### `useRegister()`

**File**: `hooks/use-register.ts`

TanStack Query mutation hook for user registration.

**Returns**: Same mutation interface as `useLogin()`

**Behavior**:

- On success: Redirects to `/sign-in` page
- On error: Error can be accessed via mutation state

**Example**:

```typescript
function SignUpForm() {
  const registerMutation = useRegister();

  const handleSubmit = (data) => {
    registerMutation.mutate({
      name: data.name,
      email: data.email,
      password: data.password,
    });
  };

  // Similar structure to login form
}
```

#### `useCurrentUser()`

**File**: `hooks/use-current-user.ts`

TanStack Query query hook for fetching current user data.

**Returns**:

- `data`: User object
- `isLoading`: Loading state
- `isError`: Error state
- `error`: Error object
- `refetch()`: Manually refetch user data

**Behavior**:

- Only runs when token exists (`enabled: !!token`)
- Caches data for 5 minutes (staleTime)
- Retains data for 10 minutes after unmount (gcTime)

**Example**:

```typescript
function UserProfile() {
  const { data: user, isLoading, refetch } = useCurrentUser();

  if (isLoading) return <Spinner />;
  if (!user) return <div>Not logged in</div>;

  return (
    <div>
      <h1>{user.name}</h1>
      <p>{user.email}</p>
      <button onClick={() => refetch()}>Refresh</button>
    </div>
  );
}
```

#### `useAuth()` - Unified Hook

**File**: `hooks/use-auth.ts`

Combines all authentication functionality into a single convenient hook.

**Returns**:

```typescript
{
  // User state
  user: User | undefined,
  isLoading: boolean,
  isAuthenticated: boolean,

  // Login
  login: (credentials) => void,
  loginAsync: (credentials) => Promise<void>,
  isLoggingIn: boolean,
  loginError: Error | null,

  // Register
  register: (userData) => void,
  registerAsync: (userData) => Promise<void>,
  isRegistering: boolean,
  registerError: Error | null,

  // User operations
  refetchUser: () => Promise<void>,

  // Logout
  logout: () => Promise<void>
}
```

**Example**:

```typescript
function MyComponent() {
  const {
    user,
    isAuthenticated,
    login,
    logout,
    isLoggingIn
  } = useAuth();

  if (!isAuthenticated) {
    return (
      <button onClick={() => login({ email, password })}>
        {isLoggingIn ? 'Logging in...' : 'Login'}
      </button>
    );
  }

  return (
    <div>
      <p>Welcome, {user?.name}!</p>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

### 4. Form Components

#### `SignInForm`

**File**: `components/sign-in-form.tsx`

Pre-built sign-in form component with validation.

**Features**:

- Email and password fields
- Form validation using Zod schema
- Error display for validation and API errors
- Loading state during submission
- Link to sign-up page

**Example**:

```typescript
import { SignInForm } from '@/features/auth/components';

function SignInPage() {
  return (
    <div>
      <h1>Sign In</h1>
      <SignInForm />
    </div>
  );
}
```

#### `SignUpForm`

**File**: `components/sign-up-form.tsx`

Pre-built sign-up form component with validation.

**Features**:

- Name, email, password, and password confirmation fields
- Password strength validation
- Password match validation
- Error display
- Loading state
- Link to sign-in page

**Example**:

```typescript
import { SignUpForm } from '@/features/auth/components';

function SignUpPage() {
  return (
    <div>
      <h1>Create Account</h1>
      <SignUpForm />
    </div>
  );
}
```

### 5. Validation Schemas

**File**: `schemas/auth.schema.ts`

Zod schemas for form validation and type inference.

**Schemas**:

- `signInSchema`: Email (valid format) + Password (min 8 chars)
- `signUpSchema`: Name (min 2 chars) + Email + Password + Confirm Password (with match validation)

**Example**:

```typescript
import { signInSchema } from '@/features/auth/schemas';

// Validate form data
const result = signInSchema.safeParse(formData);

if (result.success) {
  // Use result.data
} else {
  // Handle result.error
}

// Type inference
type SignInData = z.infer<typeof signInSchema>;
```

## Authentication Flow

### Sign-Up Flow

1. User fills out sign-up form (`SignUpForm`)
2. Form validates using `signUpSchema`
3. On submit, `useRegister()` mutation is triggered
4. `authService.register()` sends POST to `/api/v1/auth/register`
5. On success, user is redirected to `/sign-in`
6. User can now sign in with their credentials

### Sign-In Flow

1. User fills out sign-in form (`SignInForm`)
2. Form validates using `signInSchema`
3. On submit, `useLogin()` mutation is triggered
4. `authService.login()` sends OAuth2 token request
5. On success:
   - Access token is temporarily stored
   - `authService.getCurrentUser()` fetches user data
   - Token, refresh token, and user data are stored in Zustand
   - User is redirected to `/dashboard`

### Authentication Check Flow

1. Component uses `useAuth()` or `useCurrentUser()`
2. Hook reads token from Zustand store
3. If token exists, query fetches user data from API
4. If token is invalid/expired:
   - API returns 401 error
   - Auth state is cleared
   - User is redirected to sign-in

### Logout Flow

1. User clicks logout
2. `useAuth().logout()` is called
3. `authService.logout()` sends logout request to API
4. Zustand store is cleared
5. User is redirected to sign-in page

## Protected Routes

### Dashboard Layout

**File**: `shared/components/layouts/dashboard-layout.tsx`

Wraps dashboard pages and enforces authentication.

**Behavior**:

- Checks authentication on mount
- Shows loading spinner during auth check
- Redirects to `/sign-in` if not authenticated
- Renders children if authenticated

**Example**:

```typescript
// In app/(dashboard)/layout.tsx
import { DashboardLayout } from '@/shared/components/layouts';

export default function Layout({ children }) {
  return <DashboardLayout>{children}</DashboardLayout>;
}
```

## API Integration

### Base Configuration

**File**: `shared/config/api.config.ts`

```typescript
API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  VERSION: 'v1',
  TIMEOUT: 30000,
  RETRY_COUNT: 1,
  RETRY_DELAY: 1000,
};

API_ENDPOINTS = {
  AUTH: {
    TOKEN: '/auth/token', // POST: OAuth2 login
    REGISTER: '/auth/register', // POST: User registration
    ME: '/auth/me', // GET: Current user
    REFRESH: '/auth/refresh', // POST: Refresh token
    LOGOUT: '/auth/logout', // POST: Logout
  },
};
```

### API Client

**File**: `shared/lib/api-client.ts`

Centralized HTTP client with automatic:

- Auth header injection from Zustand store
- Retry logic with exponential backoff
- Error handling with typed ApiError
- JSON request/response handling

**Note**: Login endpoint uses direct fetch (not apiClient) because it requires `application/x-www-form-urlencoded` format instead of JSON.

## Type Definitions

**File**: `types/auth.types.ts`

```typescript
// User object
interface User {
  id: string;
  email: string;
  name: string;
  createdAt: string;
  updatedAt: string;
}

// Login credentials
interface LoginCredentials {
  email: string;
  password: string;
}

// Registration data
interface RegisterData {
  name: string;
  email: string;
  password: string;
}

// Token response from OAuth2 endpoint
interface TokenResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
}

// Auth store state
interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: User | null;
  setAuth: (token: string, user: User, refreshToken?: string) => void;
  setToken: (token: string) => void;
  clearAuth: () => void;
}
```

## Common Patterns

### Accessing Current User

```typescript
// In a component
const { user } = useAuth();

// In Zustand store (outside React)
const user = useAuthStore.getState().user;
```

### Checking Authentication Status

```typescript
const { isAuthenticated, isLoading } = useAuth();

if (isLoading) return <Spinner />;
if (!isAuthenticated) return <LoginPrompt />;
return <AuthenticatedContent />;
```

### Manual Token Refresh

```typescript
const { refreshToken } = useAuthStore.getState();

if (refreshToken) {
  try {
    const response = await authService.refreshToken(refreshToken);
    useAuthStore.getState().setToken(response.access_token);
  } catch (error) {
    // Refresh failed, logout user
    useAuthStore.getState().clearAuth();
    router.push('/sign-in');
  }
}
```

### Handling API Errors

```typescript
const loginMutation = useLogin();

if (loginMutation.isError) {
  const error = loginMutation.error;

  // ApiError from apiClient
  if (error instanceof ApiError) {
    console.log('Status:', error.status);
    console.log('Message:', error.message);
  }
}
```

## Testing

### Testing Components

```typescript
import { renderWithProviders } from '@/test-utils';
import { SignInForm } from './sign-in-form';

describe('SignInForm', () => {
  it('should validate email format', async () => {
    const { getByLabelText, getByText } = renderWithProviders(<SignInForm />);

    const emailInput = getByLabelText('Email');
    fireEvent.change(emailInput, { target: { value: 'invalid' } });
    fireEvent.blur(emailInput);

    expect(getByText('Please enter a valid email address')).toBeInTheDocument();
  });
});
```

### Testing Hooks

```typescript
import { renderHook } from '@testing-library/react';
import { useAuth } from './use-auth';

describe('useAuth', () => {
  it('should return authenticated state', () => {
    const { result } = renderHook(() => useAuth());

    expect(result.current.isAuthenticated).toBe(false);
  });
});
```

## Migration Notes

### From Old Auth System

The new authentication system replaces:

- ❌ `lib/auth-context.tsx` → ✅ `features/auth/hooks/use-auth.ts`
- ❌ `services/auth-service.ts` → ✅ `features/auth/services/auth.service.ts`
- ❌ `utils/auth.ts` → ✅ Zustand store + apiClient

**Key Changes**:

- React Context → Zustand for state management
- Raw fetch → TanStack Query for server state
- Manual token management → Automatic via apiClient
- Scattered auth logic → Centralized in features/auth

### Breaking Changes

1. **Hook API**: `useAuth()` return shape changed

   ```typescript
   // Old
   const { user, loading } = useAuth();

   // New
   const { user, isLoading, isAuthenticated } = useAuth();
   ```

2. **Auth Service**: Methods return promises (no callbacks)

   ```typescript
   // Old
   authService.login(credentials, onSuccess, onError);

   // New
   const response = await authService.login(credentials);
   ```

3. **Store Access**: Direct import instead of context

   ```typescript
   // Old
   const AuthContext = useContext(AuthContext);

   // New
   const token = useAuthStore((state) => state.token);
   ```

## Troubleshooting

### "User not authenticated" error

Check:

1. Token exists in Zustand store (`useAuthStore.getState().token`)
2. Token hasn't expired (check JWT payload)
3. API is receiving Authorization header
4. Backend endpoint requires authentication

### Login succeeds but user data not available

Check:

1. `/auth/me` endpoint returns user data
2. User data structure matches `User` type
3. Network tab shows successful `/auth/me` request after login
4. No errors in TanStack Query devtools

### Infinite redirect loop

Check:

1. Auth check logic in protected layouts
2. Root page redirect conditions
3. Token validity
4. Console for auth-related errors

### Token not persisting across refreshes

Check:

1. Zustand persist middleware configured
2. localStorage available (not disabled)
3. `auth-storage` key exists in localStorage
4. No errors during hydration

## Future Enhancements

- [ ] Automatic token refresh before expiration
- [ ] Remember me functionality
- [ ] Social authentication (Google, GitHub)
- [ ] Two-factor authentication
- [ ] Password reset flow
- [ ] Email verification
- [ ] Session management UI
- [ ] Role-based access control (RBAC)

## Related Documentation

- [TanStack Query Documentation](https://tanstack.com/query/latest)
- [Zustand Documentation](https://zustand-demo.pmnd.rs/)
- [Zod Documentation](https://zod.dev/)
- [Next.js App Router](https://nextjs.org/docs/app)
- [React Hook Form](https://react-hook-form.com/)

---

**Last Updated**: 2025-09-30
**Version**: 2.0.0 (Full refactoring completed)
