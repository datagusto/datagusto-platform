/**
 * Project detail page
 *
 * @description Main page displaying project details and resources.
 * Shows project header and empty content area for future features.
 *
 * @module project-detail-page
 */

'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { projectService } from '@/features/projects/services';
import type { Project } from '@/features/projects/types';
import {
  ProjectAgentsSummary,
  ProjectGuardrailsSummary,
} from '@/features/projects/components';

/**
 * Project detail page component
 *
 * @description Renders project header and empty content area.
 * Fetches project details and displays project name in header.
 *
 * **Route**: /projects/[projectId]
 *
 * **Features**:
 * - Project header with name and actions
 * - Settings and members icon buttons (placeholder)
 * - Empty content area for future implementation
 * - Loading and error states
 *
 * @example
 * ```
 * // User navigates to /projects/123e4567-e89b-12d3-a456-426614174000
 * // Sees project header and empty content area
 * ```
 */
export default function ProjectDetailPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params.projectId as string;

  const [project, setProject] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch project details
  useEffect(() => {
    let isMounted = true;

    async function fetchProject() {
      if (!projectId) return;

      try {
        setIsLoading(true);
        setError(null);

        const projectData = await projectService.getProject(projectId);

        if (!isMounted) return;

        setProject(projectData);
      } catch (err) {
        if (!isMounted) return;

        console.error('Failed to fetch project:', err);

        // Handle authentication errors by redirecting to login
        if (err instanceof Error && err.message.includes('401')) {
          router.push('/sign-in');
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load project. Please try again.'
        );
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    fetchProject();

    return () => {
      isMounted = false;
    };
  }, [projectId, router]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b bg-white">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {isLoading ? (
                <div className="h-8 w-48 bg-gray-200 animate-pulse rounded"></div>
              ) : (
                <h1 className="text-2xl font-bold">
                  {project?.name || 'Project'}
                </h1>
              )}
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
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* Project resources */}
        {!isLoading && !error && project && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Agents section */}
            <ProjectAgentsSummary projectId={projectId} />

            {/* Guardrails section */}
            <ProjectGuardrailsSummary projectId={projectId} />
          </div>
        )}
      </div>
    </div>
  );
}
