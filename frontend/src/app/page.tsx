/**
 * Root page (redirect hub)
 *
 * @description Landing page that redirects users based on authentication status.
 * Authenticated users are sent to dashboard, unauthenticated to sign-in.
 *
 * @module root-page
 */

'use client';

import { useAuth } from '@/features/auth/hooks';
import { Loading } from '@/shared/components/common';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

/**
 * Root page component
 *
 * @description Handles initial routing logic based on user authentication status.
 * This page acts as a redirect hub and should not display content to users.
 *
 * **Route**: /
 *
 * **Routing Logic**:
 * - If authenticated → Redirect to /dashboard
 * - If not authenticated → Redirect to /sign-in
 * - If loading → Show loading indicator
 *
 * **Technical Details**:
 * - Uses new useAuth hook from features/auth
 * - Implements useEffect for client-side routing
 * - No content rendering, only redirect logic
 *
 * @example
 * ```
 * // User visits site root (/)
 * // If logged in: automatically redirected to /dashboard
 * // If not logged in: automatically redirected to /sign-in
 * ```
 */
export default function RootPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      if (isAuthenticated) {
        router.push('/dashboard');
      } else {
        router.push('/sign-in');
      }
    }
  }, [isAuthenticated, isLoading, router]);

  return <Loading />;
}
