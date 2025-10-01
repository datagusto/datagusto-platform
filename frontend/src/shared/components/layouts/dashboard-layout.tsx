/**
 * Dashboard layout component
 *
 * @description Layout wrapper for authenticated dashboard pages.
 * Provides authentication check and consistent structure for dashboard-related pages.
 *
 * **Features**:
 * - Automatic authentication verification
 * - Redirect to sign-in if not authenticated
 * - Loading state display during auth check
 * - Gray background for visual consistency
 * - Responsive design
 *
 * @module dashboard-layout
 */

'use client';

import { useAuth } from '@/features/auth/hooks';
import { useAuthStore } from '@/features/auth/stores';
import { Loading } from '@/shared/components/common';
import { Sidebar } from '@/shared/components/sidebar';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

/**
 * DashboardLayout component props
 *
 * @interface DashboardLayoutProps
 */
interface DashboardLayoutProps {
  /** Child components to render within the layout */
  children: React.ReactNode;
}

/**
 * Dashboard layout component
 *
 * @description Wraps dashboard pages with authentication check and consistent layout.
 * Redirects unauthenticated users to the sign-in page.
 *
 * **Authentication Flow**:
 * 1. Check if user is authenticated using useAuth hook
 * 2. If loading, show loading spinner
 * 3. If not authenticated, redirect to /sign-in
 * 4. If authenticated, render children
 *
 * **Visual Design**:
 * - Full viewport height (min-h-screen)
 * - Gray background (bg-gray-50)
 * - Responsive padding
 *
 * **Usage**:
 * This component is typically used in layout.tsx files within dashboard route groups.
 * It ensures only authenticated users can access dashboard pages.
 *
 * @param props - Component props
 * @param props.children - Page content to display (dashboard pages, components, etc.)
 *
 * @example
 * ```tsx
 * // In app/(dashboard)/layout.tsx
 * import { DashboardLayout } from '@/shared/components/layouts';
 *
 * export default function Layout({ children }) {
 *   return <DashboardLayout>{children}</DashboardLayout>;
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Resulting structure for dashboard page
 * <DashboardLayout>
 *   <div>
 *     <h1>Dashboard</h1>
 *     <DashboardContent />
 *   </div>
 * </DashboardLayout>
 * ```
 */
export function DashboardLayout({ children }: DashboardLayoutProps) {
  const { user, isLoading, isAuthenticated } = useAuth();
  const hasHydrated = useAuthStore((state) => state._hasHydrated);
  const router = useRouter();

  useEffect(() => {
    // Wait for Zustand to hydrate from localStorage before checking auth
    if (hasHydrated && !isLoading && !isAuthenticated) {
      router.push('/sign-in');
    }
  }, [hasHydrated, isAuthenticated, isLoading, router]);

  // Show loading while hydrating or fetching user
  if (!hasHydrated || isLoading) {
    return <Loading />;
  }

  if (!isAuthenticated || !user) {
    return null;
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
