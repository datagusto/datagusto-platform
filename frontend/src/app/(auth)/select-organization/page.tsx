/**
 * Organization selection page
 *
 * @description Page for selecting organization after login/register when user belongs to multiple organizations.
 * Displays all organizations the user is a member of and allows selection.
 *
 * @module select-organization-page
 */

'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { organizationService } from '@/features/auth/services';
import { useAuthStore } from '@/features/auth/stores';
import type { UserOrganization } from '@/features/auth/types';

/**
 * Organization selection page content component
 *
 * @description Renders organization selection UI when user belongs to multiple organizations.
 * Fetches user's organizations and displays them as selectable cards.
 *
 * **Route**: /select-organization
 *
 * **Query Parameters**:
 * - from: 'login' | 'register' (identifies where user came from)
 *
 * **Features**:
 * - Displays organization name and user's role
 * - Visual feedback on hover
 * - Loading state while fetching organizations
 * - Error handling with retry
 * - Automatic navigation to dashboard after selection
 *
 * @example
 * ```
 * // User logs in with multiple organizations
 * // Redirected to /select-organization?from=login
 * // Selects organization
 * // Redirected to /dashboard
 * ```
 */
function SelectOrganizationContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const _from = searchParams.get('from') || 'login';

  const setCurrentOrganization = useAuthStore(
    (state) => state.setCurrentOrganization
  );
  const token = useAuthStore((state) => state.token);

  const [organizations, setOrganizations] = useState<UserOrganization[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch organizations on mount
  useEffect(() => {
    async function fetchOrganizations() {
      try {
        setIsLoading(true);
        setError(null);

        // Check if user is authenticated
        if (!token) {
          router.push('/sign-in');
          return;
        }

        const orgs = await organizationService.listMyOrganizations();

        // If only one organization, auto-select and redirect
        if (orgs.length === 1) {
          setCurrentOrganization(orgs[0].id);
          router.push(`/organizations/${orgs[0].id}`);
          return;
        }

        // If no organizations, show error
        if (orgs.length === 0) {
          setError('You do not belong to any organization');
          return;
        }

        setOrganizations(orgs);
      } catch (err) {
        console.error('Failed to fetch organizations:', err);
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load organizations. Please try again.'
        );
      } finally {
        setIsLoading(false);
      }
    }

    fetchOrganizations();
  }, [token, router, setCurrentOrganization]);

  // Handle organization selection
  const handleSelectOrganization = (organizationId: string) => {
    setCurrentOrganization(organizationId);
    router.push(`/organizations/${organizationId}`);
  };

  // Retry fetching organizations
  const handleRetry = () => {
    setIsLoading(true);
    setError(null);
    organizationService
      .listMyOrganizations()
      .then((orgs) => {
        setOrganizations(orgs);
        setIsLoading(false);
      })
      .catch((err) => {
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load organizations. Please try again.'
        );
        setIsLoading(false);
      });
  };

  // Get role badge color
  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'owner':
        return 'bg-purple-100 text-purple-800';
      case 'admin':
        return 'bg-blue-100 text-blue-800';
      case 'member':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-12">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Select Organization
          </h1>
          <p className="text-gray-600">
            Choose which organization you want to access
          </p>
        </div>

        {/* Loading state */}
        {isLoading && (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
          </div>
        )}

        {/* Error state */}
        {error && !isLoading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <svg
              className="w-12 h-12 text-red-600 mx-auto mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <h3 className="text-lg font-medium text-red-900 mb-2">Error</h3>
            <p className="text-red-700 mb-4">{error}</p>
            <button
              onClick={handleRetry}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Retry
            </button>
          </div>
        )}

        {/* Organization list */}
        {!isLoading && !error && organizations.length > 0 && (
          <div className="space-y-3">
            {organizations.map((org) => (
              <button
                key={org.id}
                onClick={() => handleSelectOrganization(org.id)}
                className="w-full bg-white border border-gray-200 rounded-lg p-6 hover:border-gray-900 hover:shadow-md transition-all duration-200 text-left group"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 group-hover:text-gray-900 mb-1">
                      {org.name}
                    </h3>
                    <div className="flex items-center gap-2">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleBadgeColor(org.role)}`}
                      >
                        {org.role.charAt(0).toUpperCase() + org.role.slice(1)}
                      </span>
                      {org.joined_at && (
                        <span className="text-xs text-gray-500">
                          Joined {new Date(org.joined_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                  <svg
                    className="w-6 h-6 text-gray-400 group-hover:text-gray-900 transition-colors"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Back to login link */}
        <div className="mt-6 text-center">
          <button
            onClick={() => {
              useAuthStore.getState().clearAuth();
              router.push('/sign-in');
            }}
            className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
          >
            ← Back to sign in
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Organization selection page wrapper
 *
 * @description Wraps SelectOrganizationContent with Suspense boundary to satisfy Next.js 15 requirements.
 * This is required when using useSearchParams() in a client component.
 *
 * @returns Organization selection page with proper Suspense boundary
 */
export default function SelectOrganizationPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center px-4 py-12">
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
          </div>
        </div>
      }
    >
      <SelectOrganizationContent />
    </Suspense>
  );
}
