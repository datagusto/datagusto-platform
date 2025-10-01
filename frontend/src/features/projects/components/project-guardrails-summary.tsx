/**
 * Project guardrails summary component
 *
 * @description Displays a summary list of guardrails in a project.
 * Shows recent guardrails with link to full list.
 *
 * @module project-guardrails-summary
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { guardrailService } from '@/features/guardrails/services';
import type { Guardrail } from '@/features/guardrails/types';

/**
 * Project guardrails summary props
 */
interface ProjectGuardrailsSummaryProps {
  projectId: string;
}

/**
 * Project guardrails summary component
 *
 * @description Fetches and displays recent guardrails in a project.
 */
export function ProjectGuardrailsSummary({
  projectId,
}: ProjectGuardrailsSummaryProps) {
  const router = useRouter();
  const [guardrails, setGuardrails] = useState<Guardrail[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function fetchGuardrails() {
      try {
        setIsLoading(true);
        setError(null);

        const response = await guardrailService.listGuardrails(projectId, {
          page: 1,
          page_size: 5,
          is_active: true,
          is_archived: false,
        });

        if (!isMounted) return;

        setGuardrails(response.items);
        setTotal(response.total);
      } catch (err) {
        if (!isMounted) return;

        console.error('Failed to fetch guardrails:', err);
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load guardrails. Please try again.'
        );
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    fetchGuardrails();

    return () => {
      isMounted = false;
    };
  }, [projectId]);

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex justify-center items-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-600">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Guardrails</h2>
          <p className="text-sm text-gray-600 mt-1">
            {total} guardrail{total !== 1 ? 's' : ''} in this project
          </p>
        </div>
        <button
          onClick={() => router.push(`/projects/${projectId}/guardrails`)}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          View all →
        </button>
      </div>

      {/* Content */}
      {guardrails.length === 0 ? (
        <div className="text-center py-12 px-6">
          <svg
            className="w-12 h-12 text-gray-400 mx-auto mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
            />
          </svg>
          <h4 className="text-sm font-medium text-gray-900 mb-2">
            No guardrails yet
          </h4>
          <p className="text-sm text-gray-600 mb-4">
            Get started by creating your first guardrail
          </p>
          <button
            onClick={() => router.push(`/projects/${projectId}/guardrails`)}
            className="px-4 py-2 bg-black text-white rounded-md hover:bg-gray-800 transition-colors text-sm inline-flex items-center gap-2"
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
        <div className="divide-y divide-gray-200">
          {guardrails.map((guardrail) => (
            <div
              key={guardrail.id}
              className="px-6 py-4 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium text-gray-900 truncate">
                    {guardrail.name}
                  </h3>
                  <div className="flex items-center gap-3 mt-1">
                    <p className="text-xs text-gray-500">
                      Created{' '}
                      {new Date(guardrail.created_at).toLocaleDateString()}
                    </p>
                    <span className="text-xs text-gray-400">•</span>
                    <p className="text-xs text-gray-500">
                      {guardrail.assigned_agent_count} agent
                      {guardrail.assigned_agent_count !== 1 ? 's' : ''}
                    </p>
                  </div>
                </div>
                <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800 flex-shrink-0 ml-4">
                  Active
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
