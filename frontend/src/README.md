# Frontend Architecture Documentation

## Overview

This document provides comprehensive documentation for the datagusto-v2 frontend architecture. The application is built using Next.js 15 with App Router, following a feature-based architecture pattern for scalability and maintainability.

---

## Technology Stack

### Core Technologies

- **Framework**: Next.js 15.3+ (App Router)
- **Language**: TypeScript 5+
- **UI Library**: React 19
- **Styling**: Tailwind CSS 3.4+

### State Management

- **Client State**: Zustand 5.0+ with middleware (devtools, persist)
- **Server State**: TanStack Query 5.80+ (React Query)
- **Form State**: react-hook-form 7.54+ with Zod validation

### UI Components

- **Component Library**: Radix UI primitives
- **Utility Library**: shadcn/ui components
- **Icons**: lucide-react

---

## Directory Structure

```
src/
├── features/                    # Feature-based modules (domain logic)
│   ├── auth/                    # Authentication feature
│   │   ├── components/          # Auth-specific components
│   │   ├── hooks/               # Auth-specific hooks (TanStack Query)
│   │   ├── stores/              # Auth state (Zustand)
│   │   ├── services/            # Auth API services
│   │   ├── schemas/             # Zod validation schemas
│   │   ├── types/               # TypeScript type definitions
│   │   └── README.md            # Feature documentation
│   ├── projects/                # Project management feature (future)
│   ├── guardrails/              # Guardrail feature (future)
│   └── data-quality/            # Data quality analysis feature (future)
├── shared/                      # Shared resources across features
│   ├── components/              # Shared components
│   │   ├── ui/                  # shadcn/ui components
│   │   ├── layouts/             # Layout components
│   │   └── common/              # Common UI components (Loading, ErrorMessage)
│   ├── hooks/                   # Shared custom hooks
│   ├── lib/                     # Library configurations
│   │   ├── query-client.ts      # TanStack Query setup
│   │   ├── api-client.ts        # HTTP client
│   │   └── utils.ts             # Utility functions
│   ├── config/                  # Configuration files
│   │   ├── api.config.ts        # API configuration
│   │   ├── routes.config.ts     # Route definitions
│   │   └── constants.ts         # Global constants
│   └── types/                   # Shared type definitions
├── app/                         # Next.js App Router (pages & layouts)
│   ├── (auth)/                  # Auth route group
│   │   ├── layout.tsx           # Auth layout
│   │   ├── sign-in/page.tsx     # Sign-in page
│   │   └── sign-up/page.tsx     # Sign-up page
│   ├── (dashboard)/             # Protected dashboard route group
│   │   ├── layout.tsx           # Dashboard layout (with auth check)
│   │   └── page.tsx             # Dashboard home page
│   ├── layout.tsx               # Root layout (Providers)
│   ├── page.tsx                 # Root page (redirect logic)
│   └── globals.css              # Global styles
├── middleware.ts                # Next.js middleware
└── README.md                    # This file
```

---

## Architecture Principles

### 1. Feature-Based Organization

Each feature is self-contained with its own:

- Components (UI)
- Hooks (data fetching & business logic)
- Stores (local state)
- Services (API communication)
- Schemas (validation)
- Types (TypeScript definitions)

**Benefits**:

- High cohesion within features
- Low coupling between features
- Easy to add/remove features
- Clear ownership and responsibility

### 2. Separation of Concerns

#### Client State vs Server State

- **Client State (Zustand)**: UI state, user preferences, authentication tokens
- **Server State (TanStack Query)**: API data, cache management, synchronization

**Example**:

```typescript
// Client State: Auth token (managed by Zustand)
const token = useAuthStore((state) => state.token);

// Server State: User data (managed by TanStack Query)
const { data: user } = useQuery({
  queryKey: ['currentUser'],
  queryFn: () => authService.getCurrentUser(),
});
```

### 3. Single Responsibility

Each module has a single, well-defined responsibility:

- **Components**: UI rendering only
- **Hooks**: Business logic and data fetching
- **Services**: API communication
- **Stores**: State management
- **Schemas**: Validation rules

---

## Path Aliases

Configure imports using TypeScript path aliases for better readability:

```typescript
// tsconfig.json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"],
      "@/features/*": ["./src/features/*"],
      "@/shared/*": ["./src/shared/*"],
      "@/app/*": ["./src/app/*"]
    }
  }
}
```

**Usage**:

```typescript
// ✅ Good: Use path aliases
import { useAuth } from '@/features/auth/hooks';
import { Button } from '@/shared/components/ui/button';

// ❌ Bad: Relative paths
import { useAuth } from '../../../features/auth/hooks';
```

---

## State Management Guide

### Zustand (Client State)

Use Zustand for client-side state that doesn't come from the server.

**When to use**:

- Authentication tokens
- UI preferences (theme, language)
- Modal/drawer open state
- Selected items

**Example**:

```typescript
// src/features/auth/stores/auth.store.ts
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface AuthState {
  token: string | null;
  setToken: (token: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set) => ({
        token: null,
        setToken: (token) => set({ token }),
        clearAuth: () => set({ token: null }),
      }),
      { name: 'auth-storage' }
    ),
    { name: 'AuthStore' }
  )
);

// Usage in components
function MyComponent() {
  const token = useAuthStore((state) => state.token);
  return <div>Token: {token}</div>;
}
```

### TanStack Query (Server State)

Use TanStack Query for data from APIs.

**When to use**:

- Fetching data from APIs
- Mutations (create, update, delete)
- Caching and synchronization
- Background refetching

**Example**:

```typescript
// src/features/auth/hooks/use-current-user.ts
import { useQuery } from '@tanstack/react-query';
import { authService } from '../services';

export function useCurrentUser() {
  return useQuery({
    queryKey: ['currentUser'],
    queryFn: () => authService.getCurrentUser(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });
}

// Usage in components
function UserProfile() {
  const { data: user, isLoading, error } = useCurrentUser();

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return <div>Hello, {user.name}!</div>;
}
```

---

## Form Management

### react-hook-form + Zod

All forms use react-hook-form with Zod schemas for type-safe validation.

**Pattern**:

```typescript
// 1. Define schema
import { z } from 'zod';

export const signInSchema = z.object({
  email: z.string().email({ message: 'Invalid email address' }),
  password: z.string().min(8, { message: 'Password must be at least 8 characters' }),
});

export type SignInFormData = z.infer<typeof signInSchema>;

// 2. Use in component
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

function SignInForm() {
  const { register, handleSubmit, formState: { errors } } = useForm<SignInFormData>({
    resolver: zodResolver(signInSchema),
  });

  const onSubmit = (data: SignInFormData) => {
    console.log(data); // Type-safe!
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('email')} />
      {errors.email && <span>{errors.email.message}</span>}
      {/* ... */}
    </form>
  );
}
```

---

## API Communication

### API Client Pattern

All API calls go through a centralized API client with:

- Automatic authentication headers
- Error handling
- Type safety

**Example**:

```typescript
// src/shared/lib/api-client.ts
export async function apiClient<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const token = useAuthStore.getState().token;

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'API Error');
  }

  return response.json();
}

// Usage in service
export const authService = {
  async getCurrentUser(): Promise<User> {
    return apiClient<User>('/api/v1/auth/me');
  },
};
```

---

## Common Components

### Loading Component

Reusable loading indicator with consistent styling:

```typescript
// src/shared/components/common/loading.tsx
import { Loading } from '@/shared/components/common';

// Full screen loading (default)
<Loading />

// Inline loading with custom message
<Loading message="Loading data..." fullScreen={false} />
```

### ErrorMessage Component

Reusable error display with proper ARIA attributes:

```typescript
// src/shared/components/common/error-message.tsx
import { ErrorMessage } from '@/shared/components/common';

// Display error object
<ErrorMessage error={error} />

// Display string error with custom title
<ErrorMessage error="Something went wrong" title="Error" />
```

---

## Adding a New Feature

Follow these steps to add a new feature (e.g., "projects"):

### 1. Create Feature Directory

```bash
mkdir -p src/features/projects/{components,hooks,stores,services,schemas,types}
```

### 2. Define Types

```typescript
// src/features/projects/types/project.types.ts
export interface Project {
  id: string;
  name: string;
  description: string;
  createdAt: string;
}
```

### 3. Create API Service

```typescript
// src/features/projects/services/project.service.ts
import { apiClient } from '@/shared/lib/api-client';
import type { Project } from '../types';

export const projectService = {
  async getProjects(): Promise<Project[]> {
    return apiClient<Project[]>('/api/v1/projects');
  },
};
```

### 4. Create Hooks (TanStack Query)

```typescript
// src/features/projects/hooks/use-projects.ts
import { useQuery } from '@tanstack/react-query';
import { projectService } from '../services';

export function useProjects() {
  return useQuery({
    queryKey: ['projects'],
    queryFn: () => projectService.getProjects(),
  });
}
```

### 5. Create Components

```typescript
// src/features/projects/components/project-list.tsx
import { useProjects } from '../hooks';

export function ProjectList() {
  const { data: projects, isLoading } = useProjects();

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      {projects?.map((project) => (
        <div key={project.id}>{project.name}</div>
      ))}
    </div>
  );
}
```

### 6. Add Route

```typescript
// src/app/(dashboard)/projects/page.tsx
import { ProjectList } from '@/features/projects/components';

export default function ProjectsPage() {
  return (
    <div>
      <h1>Projects</h1>
      <ProjectList />
    </div>
  );
}
```

### 7. Create Feature README

```markdown
// src/features/projects/README.md

# Projects Feature

This feature handles project management...
```

---

## Development Workflow

### Starting Development Server

```bash
cd frontend
npm run dev
```

Access at: http://localhost:3000

### Building for Production

```bash
npm run build
npm run start
```

### Type Checking

```bash
npx tsc --noEmit
```

### Linting

```bash
npm run lint
```

### Code Formatting

```bash
# Format all files
npm run format

# Check formatting without making changes
npm run format:check
```

**Prettier Configuration** (`.prettierrc.json`):

- Single quotes for strings
- Semicolons required
- 2 spaces indentation
- 80 character line width
- ES5 trailing commas

### Testing

```bash
npm test
npm run test:coverage
```

### Bundle Analysis

```bash
npm run analyze
```

Opens webpack bundle analyzer to inspect bundle sizes.

---

## Code Quality Standards

### ESLint Configuration

Custom rules in `eslint.config.mjs`:

- **Underscore Pattern**: Variables prefixed with `_` are allowed to be unused
  - Example: `const { confirmPassword: _confirmPassword, ...rest } = data;`
- **TypeScript Strict**: No explicit `any` types (use `unknown` instead)
- **Next.js Rules**: Following Next.js and TypeScript best practices

### TypeScript

- **Strict mode**: Always enabled
- **Type inference**: Prefer inference over explicit types when obvious
- **No `any`**: Use `unknown` for truly unknown types
- **Null handling**: Use optional chaining `?.` and nullish coalescing `??`

### Documentation

All functions must have JSDoc comments:

````typescript
/**
 * Authenticates a user with email and password
 *
 * @description Sends credentials to the backend API and returns JWT tokens.
 * Stores the access token in Zustand store for subsequent requests.
 *
 * @param credentials - User login credentials
 * @returns Promise with token response including access_token and refresh_token
 * @throws {Error} When authentication fails or network error occurs
 *
 * @example
 * ```typescript
 * const tokens = await authService.login({
 *   email: 'user@example.com',
 *   password: 'securePassword123'
 * });
 * console.log(tokens.access_token); // eyJhbGc...
 * ```
 */
export async function login(
  credentials: LoginCredentials
): Promise<TokenResponse> {
  // Implementation
}
````

### Component Structure

````typescript
/**
 * Sign-in form component with email/password validation
 *
 * @description Provides a form for user authentication with real-time validation
 * using Zod schema. Handles loading states and error messages.
 *
 * @example
 * ```tsx
 * <SignInForm />
 * ```
 */
export function SignInForm() {
  // Hooks
  const loginMutation = useLogin();
  const { register, handleSubmit } = useForm();

  // Event handlers
  const onSubmit = (data: SignInFormData) => {
    loginMutation.mutate(data);
  };

  // Render
  return <form onSubmit={handleSubmit(onSubmit)}>...</form>;
}
````

---

## Performance Best Practices

### 1. Selective Zustand Subscriptions

```typescript
// ✅ Good: Subscribe to specific state
const token = useAuthStore((state) => state.token);

// ❌ Bad: Subscribe to entire store
const store = useAuthStore();
```

### 2. TanStack Query Optimization

```typescript
// Configure staleTime to reduce unnecessary refetches
useQuery({
  queryKey: ['data'],
  queryFn: fetchData,
  staleTime: 5 * 60 * 1000, // 5 minutes
});
```

### 3. Code Splitting

Use dynamic imports for large features:

```typescript
const HeavyComponent = dynamic(() => import('./HeavyComponent'), {
  loading: () => <Spinner />,
});
```

---

## Performance Metrics

### Current Bundle Sizes (Production Build)

**First Load JS**: 101 kB ✅ (Well under Next.js recommended 170 kB)

**Route Sizes**:

- `/` (Root page): 117 kB
- `/dashboard`: 101 kB
- `/sign-in`: 144 kB
- `/sign-up`: 144 kB

**Main Chunks**:

- `chunks/4bd1b696-d16b3ed0e927b318.js`: 53.2 kB
- `chunks/684-e2394bb2ab3b5633.js`: 45.9 kB
- Middleware: 33.2 kB

**Analysis**: Bundle sizes are optimal. Auth pages are larger due to forms and validation libraries, which is expected and acceptable.

---

## Debugging

### TanStack Query DevTools

Automatically enabled in development:

```typescript
// src/app/layout.tsx
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

export default function RootLayout({ children }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

Access: Click the React Query icon in the bottom-right corner

### Zustand Redux DevTools

Open Redux DevTools in your browser to inspect Zustand stores.

---

## Security Considerations

### Authentication

- Tokens stored in Zustand with localStorage persistence (migrate to HttpOnly cookies in future)
- Automatic token inclusion in API requests
- Token expiration handling with automatic logout

### Environment Variables

Never commit secrets. Use `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_VERSION=v1
```

---

## Troubleshooting

### Common Issues

**Issue**: "Cannot find module '@/features/...'"
**Solution**: Run `npx tsc --noEmit` to ensure path aliases are configured correctly

**Issue**: TanStack Query not caching
**Solution**: Ensure `queryKey` is consistent across components

**Issue**: Zustand state not persisting
**Solution**: Check that `persist` middleware is configured with correct storage name

---

## Migration Notes

### Phase 2: Feature-Based Architecture Migration (Completed)

**React Context → Zustand**:

- Removed `src/lib/auth-context.tsx`
- Created `src/features/auth/stores/auth.store.ts` with persist + devtools middleware
- Performance improved with selective subscriptions

**Raw fetch → TanStack Query**:

- All API calls now use `useQuery` or `useMutation`
- Automatic caching (5min staleTime, 10min gcTime) and retry logic
- Better error handling and loading states

**Authentication Architecture**:

- Feature-based structure: `features/auth/{components,hooks,stores,services,schemas,types}`
- Zod schemas with base-first design pattern
- Type-safe API client with automatic token injection
- Client-side auth checks in layouts (middleware prepared for future HttpOnly cookies)

### Phase 3: Cleanup (Completed)

- Deleted old auth files: `auth-context.tsx`, `auth-service.ts`, `utils/auth.ts`, `types/auth.ts`
- Created common components: `Loading`, `ErrorMessage`
- Updated middleware with comprehensive documentation

### Phase 5: Code Quality & Performance (Completed)

- Configured Prettier with consistent formatting rules
- Enhanced ESLint rules (underscore pattern for unused vars)
- Verified bundle sizes: 101 kB First Load JS ✅
- All TypeScript `any` types replaced with `unknown`
- Comprehensive JSDoc documentation

---

## Contributing

### Before Committing

1. Run formatter: `npm run format`
2. Run type check: `npx tsc --noEmit`
3. Run linter: `npm run lint`
4. Run tests: `npm test`
5. Update documentation if adding new features

### Commit Message Format

Follow Conventional Commits:

```bash
feat(auth): add password reset functionality
fix(api): handle null response in user query
docs(readme): update architecture documentation
```

---

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Zustand Documentation](https://docs.pmnd.rs/zustand)
- [TanStack Query Documentation](https://tanstack.com/query/latest)
- [react-hook-form Documentation](https://react-hook-form.com/)
- [Zod Documentation](https://zod.dev/)

---

## License

Internal project - datagusto-v2 frontend
