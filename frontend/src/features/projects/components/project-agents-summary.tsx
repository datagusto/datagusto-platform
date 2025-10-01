/**
 * Project agents summary component
 *
 * @description Displays a summary list of agents in a project.
 * Shows recent agents with link to full list.
 *
 * @module project-agents-summary
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { agentService } from '@/features/agents/services';
import type { Agent } from '@/features/agents/types';

/**
 * Project agents summary props
 */
interface ProjectAgentsSummaryProps {
  projectId: string;
}

/**
 * Project agents summary component
 *
 * @description Fetches and displays recent agents in a project.
 */
export function ProjectAgentsSummary({ projectId }: ProjectAgentsSummaryProps) {
  const router = useRouter();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function fetchAgents() {
      try {
        setIsLoading(true);
        setError(null);

        const response = await agentService.listAgents(projectId, {
          page: 1,
          page_size: 5,
          is_active: true,
          is_archived: false,
        });

        if (!isMounted) return;

        setAgents(response.items);
        setTotal(response.total);
      } catch (err) {
        if (!isMounted) return;

        console.error('Failed to fetch agents:', err);
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load agents. Please try again.'
        );
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    fetchAgents();

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
          <h2 className="text-lg font-semibold text-gray-900">Agents</h2>
          <p className="text-sm text-gray-600 mt-1">
            {total} agent{total !== 1 ? 's' : ''} in this project
          </p>
        </div>
        <button
          onClick={() => router.push(`/projects/${projectId}/agents`)}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          View all →
        </button>
      </div>

      {/* Content */}
      {agents.length === 0 ? (
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
              d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
            />
          </svg>
          <h4 className="text-sm font-medium text-gray-900 mb-2">
            No agents yet
          </h4>
          <p className="text-sm text-gray-600 mb-4">
            Get started by creating your first agent
          </p>
          <button
            onClick={() => router.push(`/projects/${projectId}/agents`)}
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
            Create First Agent
          </button>
        </div>
      ) : (
        <div className="divide-y divide-gray-200">
          {agents.map((agent) => (
            <button
              key={agent.id}
              onClick={() =>
                router.push(`/projects/${projectId}/agents/${agent.id}`)
              }
              className="w-full px-6 py-4 hover:bg-gray-50 transition-colors text-left"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium text-gray-900 truncate">
                    {agent.name}
                  </h3>
                  <p className="text-xs text-gray-500 mt-1">
                    Created {new Date(agent.created_at).toLocaleDateString()}
                  </p>
                </div>
                <svg
                  className="w-5 h-5 text-gray-400 flex-shrink-0 ml-4"
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
    </div>
  );
}
