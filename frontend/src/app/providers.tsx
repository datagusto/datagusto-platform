/**
 * Application providers component
 *
 * @description Wraps the application with necessary providers for state management.
 * This component is a Client Component and provides:
 * - TanStack Query (React Query) for server state management
 * - React Query DevTools for debugging (development only)
 *
 * **State Management**:
 * - Server state: TanStack Query (React Query)
 * - Client state: Zustand (used directly in components, no provider needed)
 *
 * @module providers
 */

'use client';

import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { queryClient } from '@/shared/lib/query-client';

/**
 * Providers component
 *
 * @description Wraps children with all application-level providers.
 * Must be used in the root layout to provide context to all pages.
 *
 * **Current Providers**:
 * - QueryClientProvider: Enables TanStack Query for all components
 * - ReactQueryDevtools: Development tool for inspecting queries (auto-removed in production)
 *
 * **Architecture Note**:
 * - This component is marked as 'use client' because providers like QueryClientProvider
 *   require client-side JavaScript. The root layout remains a Server Component.
 * - Zustand stores don't require a provider; they can be imported and used directly
 *   in any component, which simplifies the architecture.
 *
 * @param props - Component props
 * @param props.children - Child components to wrap with providers
 *
 * @example
 * ```tsx
 * // In app/layout.tsx
 * import { Providers } from './providers';
 *
 * export default function RootLayout({ children }) {
 *   return (
 *     <html lang="en">
 *       <body>
 *         <Providers>
 *           {children}
 *         </Providers>
 *       </body>
 *     </html>
 *   );
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Using TanStack Query in a component
 * function MyComponent() {
 *   const { data } = useQuery({
 *     queryKey: ['data'],
 *     queryFn: fetchData,
 *   });
 *
 *   return <div>{data}</div>;
 * }
 * ```
 */
export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}

      {/*
        React Query DevTools
        - Only loads in development mode (automatically tree-shaken in production)
        - Provides visual debugging interface for queries and mutations
        - Access by clicking the React Query icon in bottom-right corner
        - Shows query keys, cached data, fetch status, and refetch controls
      */}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
