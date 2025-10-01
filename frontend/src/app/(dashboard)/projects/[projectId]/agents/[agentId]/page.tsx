/**
 * Agent detail page
 *
 * @description Main page displaying agent details and related resources.
 * Shows agent header and empty content area for future features.
 *
 * @module agent-detail-page
 */

'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { agentService } from '@/features/agents/services';
import { APIKeyList, AgentGuardrailList } from '@/features/agents/components';
import type { Agent } from '@/features/agents/types';

/**
 * Agent detail page component
 *
 * @description Renders agent header and empty content area.
 * Fetches agent details and displays agent name in header.
 *
 * **Route**: /projects/[projectId]/agents/[agentId]
 *
 * **Features**:
 * - Agent header with name and actions
 * - Settings icon button (placeholder)
 * - Empty content area for future implementation (API keys, Guardrails, Traces)
 * - Loading and error states
 *
 * @example
 * ```
 * // User navigates to /projects/123/agents/456
 * // Sees agent header and empty content area
 * ```
 */
export default function AgentDetailPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params.projectId as string;
  const agentId = params.agentId as string;

  const [agent, setAgent] = useState<Agent | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch agent details
  useEffect(() => {
    let isMounted = true;

    async function fetchAgent() {
      if (!projectId || !agentId) return;

      try {
        setIsLoading(true);
        setError(null);

        const agentData = await agentService.getAgent(agentId);

        if (!isMounted) return;

        setAgent(agentData);
      } catch (err) {
        if (!isMounted) return;

        console.error('Failed to fetch agent:', err);

        // Handle authentication errors by redirecting to login
        if (err instanceof Error && err.message.includes('401')) {
          router.push('/sign-in');
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load agent. Please try again.'
        );
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    fetchAgent();

    return () => {
      isMounted = false;
    };
  }, [projectId, agentId, router]);

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
                  {agent?.name || 'Agent'}
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

        {/* Agent content */}
        {!isLoading && !error && agent && (
          <div className="space-y-8">
            {/* API Keys Section */}
            <section>
              <APIKeyList agentId={agentId} />
            </section>

            {/* Guardrails Section */}
            <section>
              <AgentGuardrailList agentId={agentId} projectId={projectId} />
            </section>

            {/* Traces Section (Coming Soon) */}
            <section>
              <h3 className="text-lg font-semibold mb-4">Traces</h3>
              <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
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
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
                <h4 className="text-sm font-medium text-gray-900 mb-2">
                  Traces Coming Soon
                </h4>
                <p className="text-sm text-gray-600">
                  Agent trace history and analysis will be available here
                </p>
              </div>
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
