/**
 * Organization projects page
 *
 * @description Main page displaying all projects within an organization.
 * Shows project list in a grid layout similar to Langfuse UI.
 *
 * @module organization-projects-page
 */

'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/features/auth/stores';
import { organizationService } from '@/features/auth/services';
import { projectService } from '@/features/projects/services';
import { CreateProjectDialog } from '@/features/projects/components';

/**
 * Organization projects page component
 *
 * @description Renders organization header and project grid.
 * Fetches projects for the current organization and displays them as cards.
 *
 * **Route**: /organizations/[organizationId]
 *
 * **Features**:
 * - Organization header with name and actions
 * - Project grid layout with cards
 * - "New project" button (placeholder)
 * - "Go to project" navigation
 * - Loading and error states
 *
 * @example
 * ```
 * // User navigates to /organizations/123e4567-e89b-12d3-a456-426614174000
 * // Sees organization header and list of projects
 * ```
 */
export default function OrganizationProjectsPage() {
  const router = useRouter();
  const params = useParams();
  const organizationId = params.organizationId as string;

  const currentOrganizationId = useAuthStore(
    (state) => state.currentOrganizationId
  );
  const setCurrentOrganization = useAuthStore(
    (state) => state.setCurrentOrganization
  );

  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  // Sync organization ID with Zustand store
  useEffect(() => {
    if (organizationId && organizationId !== currentOrganizationId) {
      setCurrentOrganization(organizationId);
    }
  }, [organizationId, currentOrganizationId, setCurrentOrganization]);

  // Fetch organization details using TanStack Query
  const {
    data: organization,
    isLoading: isLoadingOrg,
    error: orgError,
  } = useQuery({
    queryKey: ['organization', currentOrganizationId],
    queryFn: () =>
      currentOrganizationId
        ? organizationService.getOrganization(currentOrganizationId)
        : Promise.reject(new Error('No organization ID')),
    enabled: !!currentOrganizationId,
    retry: 1,
  });

  // Fetch projects using TanStack Query
  const {
    data: projectsResponse,
    isLoading: isLoadingProjects,
    error: projectsError,
  } = useQuery({
    queryKey: ['projects', currentOrganizationId],
    queryFn: () =>
      projectService.listProjects({
        is_active: true,
        is_archived: false,
      }),
    enabled: !!currentOrganizationId,
    retry: 1,
  });

  // Handle authentication errors
  useEffect(() => {
    if (orgError instanceof Error && orgError.message.includes('401')) {
      router.push('/sign-in');
    }
  }, [orgError, router]);

  const isLoading = isLoadingOrg || isLoadingProjects;
  const error = orgError || projectsError;
  const projects = projectsResponse?.items || [];
  const organizationName = organization?.name || '';

  // Handle project navigation
  const handleGoToProject = (projectId: string) => {
    router.push(`/projects/${projectId}`);
  };

  // Handle dialog close
  const handleDialogClose = (open: boolean) => {
    setCreateDialogOpen(open);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b bg-white">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">{organizationName}</h1>
            </div>

            <div className="flex items-center gap-3">
              {/* Settings icon - TODO: Implement settings functionality */}
              {/* <button className="p-2 text-gray-600 hover:text-gray-900 transition-colors">
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                </svg>
              </button> */}

              {/* Members icon - TODO: Implement members management */}
              {/* <button className="p-2 text-gray-600 hover:text-gray-900 transition-colors">
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                  />
                </svg>
              </button> */}

              {/* New project button */}
              <button
                onClick={() => setCreateDialogOpen(true)}
                className="px-4 py-2 bg-black text-white rounded-md hover:bg-gray-800 transition-colors flex items-center gap-2"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                New project
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
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
            <p className="text-red-700">
              {error instanceof Error
                ? error.message
                : 'Failed to load data. Please try again.'}
            </p>
          </div>
        )}

        {/* Projects grid */}
        {!isLoading && !error && (
          <>
            {projects.length === 0 ? (
              <div className="text-center py-12">
                <svg
                  className="w-16 h-16 text-gray-400 mx-auto mb-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
                  />
                </svg>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No projects yet
                </h3>
                <p className="text-gray-600 mb-4">
                  Get started by creating your first project
                </p>
                <button
                  onClick={() => setCreateDialogOpen(true)}
                  className="px-4 py-2 bg-black text-white rounded-md hover:bg-gray-800 transition-colors"
                >
                  Create project
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {projects.map((project) => (
                  <div
                    key={project.id}
                    className="bg-white border border-gray-200 rounded-lg p-6 hover:border-gray-900 hover:shadow-md transition-all duration-200"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {project.name}
                      </h3>
                      {/* Settings icon - TODO: Implement project settings functionality */}
                      {/* <button className="p-1 text-gray-400 hover:text-gray-900 transition-colors">
                        <svg
                          className="w-5 h-5"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                          />
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                          />
                        </svg>
                      </button> */}
                    </div>

                    <button
                      onClick={() => handleGoToProject(project.id)}
                      className="w-full px-4 py-2 bg-gray-100 text-gray-900 rounded-md hover:bg-gray-200 transition-colors"
                    >
                      Go to project
                    </button>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {/* Create Project Dialog */}
      <CreateProjectDialog
        open={createDialogOpen}
        onOpenChange={handleDialogClose}
      />
    </div>
  );
}
