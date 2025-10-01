/**
 * Project guardrails page
 *
 * @description Page displaying guardrails within a project.
 * Shows project header and guardrail list.
 *
 * @module project-guardrails-page
 */

'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { projectService } from '@/features/projects/services';
import { guardrailService } from '@/features/guardrails/services';
import type { Project } from '@/features/projects/types';
import type { Guardrail } from '@/features/guardrails/types';

export default function ProjectGuardrailsPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params.projectId as string;

  const [project, setProject] = useState<Project | null>(null);
  const [guardrails, setGuardrails] = useState<Guardrail[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function fetchData() {
      if (!projectId) return;

      try {
        setIsLoading(true);
        setError(null);

        const [projectData, guardrailsResponse] = await Promise.all([
          projectService.getProject(projectId),
          guardrailService.listGuardrails(projectId, {
            is_active: true,
            is_archived: false,
          }),
        ]);

        if (!isMounted) return;

        setProject(projectData);
        setGuardrails(guardrailsResponse.items);
      } catch (err) {
        if (!isMounted) return;

        console.error('Failed to fetch data:', err);

        if (err instanceof Error && err.message.includes('401')) {
          router.push('/sign-in');
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load data. Please try again.'
        );
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    fetchData();

    return () => {
      isMounted = false;
    };
  }, [projectId, router]);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="border-b bg-white">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {isLoading ? (
                <div className="h-8 w-48 bg-gray-200 animate-pulse rounded"></div>
              ) : (
                <h1 className="text-2xl font-bold">{project?.name || 'Project'}</h1>
              )}
            </div>
            <div className="flex items-center gap-3">
              {!isLoading && project && (
                <button
                  onClick={() => router.push(`/projects/${projectId}/guardrails/new`)}
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
                  Create Guardrail
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {isLoading && (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
          </div>
        )}

        {error && !isLoading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <svg className="w-12 h-12 text-red-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <h3 className="text-lg font-medium text-red-900 mb-2">Error</h3>
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {!isLoading && !error && project && (
          <>
            {guardrails.length === 0 ? (
              <div className="text-center py-12">
                <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No guardrails yet</h3>
                <p className="text-gray-600 mb-4">Get started by creating your first guardrail</p>
                <button
                  onClick={() => router.push(`/projects/${projectId}/guardrails/new`)}
                  className="px-4 py-2 bg-black text-white rounded-md hover:bg-gray-800 transition-colors inline-flex items-center gap-2"
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
                  Create First Guardrail
                </button>
              </div>
            ) : (
              <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Agents</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {guardrails.map((guardrail) => (
                      <tr key={guardrail.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{guardrail.name}</div>
                          <div className="text-sm text-gray-500">{guardrail.id}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Active</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {guardrail.assigned_agent_count} agent{guardrail.assigned_agent_count !== 1 ? 's' : ''}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(guardrail.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
