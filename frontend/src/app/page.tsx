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
import { useAuthStore } from '@/features/auth/stores';
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
 * - If authenticated with selected organization → Redirect to /organizations/{organizationId}
 * - If authenticated without selected organization → Redirect to /select-organization
 * - If not authenticated → Redirect to /sign-in
 * - If loading → Show loading indicator
 *
 * **Technical Details**:
 * - Uses useAuth hook from features/auth
 * - Uses useAuthStore to check current organization
 * - Implements useEffect for client-side routing
 * - No content rendering, only redirect logic
 * - Matches login success redirect behavior
 *
 * @example
 * ```
 * // User visits site root (/)
 * // If logged in with organization: automatically redirected to /organizations/{orgId}
 * // If logged in without organization: automatically redirected to /select-organization
 * // If not logged in: automatically redirected to /sign-in
 * ```
 */
export default function RootPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const currentOrganizationId = useAuthStore(
    (state) => state.currentOrganizationId
  );

  useEffect(() => {
    if (!isLoading) {
      if (isAuthenticated) {
        // ログイン成功時と同じロジックで組織情報を確認してリダイレクト
        if (currentOrganizationId) {
          // 組織が既に選択されている → プロジェクト一覧へ
          router.push(`/organizations/${currentOrganizationId}`);
        } else {
          // 組織が未選択 → 組織選択画面へ
          router.push('/select-organization');
        }
      } else {
        router.push('/sign-in');
      }
    }
  }, [isAuthenticated, isLoading, currentOrganizationId, router]);

  return <Loading />;
}
