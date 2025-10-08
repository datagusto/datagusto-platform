/**
 * Agent Guardrail list component
 *
 * @description Displays list of guardrails assigned to an agent.
 * Allows assigning new guardrails and unassigning existing ones.
 *
 * @module agent-guardrail-list
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { get } from '@/shared/lib/api-client';
import type { Guardrail } from '@/features/guardrails/types';
import { AssignGuardrailDialog } from './assign-guardrail-dialog';
import { useAssignGuardrail } from '../hooks/use-assign-guardrail';
import { useUnassignGuardrail } from '../hooks/use-unassign-guardrail';

/**
 * Agent Guardrail list props
 */
interface AgentGuardrailListProps {
  agentId: string;
  projectId: string;
}

/**
 * Guardrail list response type
 */
interface GuardrailListResponse {
  items: Guardrail[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Agent Guardrail list component
 *
 * @description Fetches and displays guardrails assigned to an agent.
 * Provides assign and unassign functionality.
 */
export function AgentGuardrailList({
  agentId,
  projectId,
}: AgentGuardrailListProps) {
  const [guardrails, setGuardrails] = useState<Guardrail[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const assignMutation = useAssignGuardrail();
  const unassignMutation = useUnassignGuardrail();

  const fetchGuardrails = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await get<GuardrailListResponse>(
        `/guardrails/agents/${agentId}/guardrails`
      );

      setGuardrails(response.items);
    } catch (err) {
      console.error('Failed to fetch guardrails:', err);
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to load guardrails. Please try again.'
      );
    } finally {
      setIsLoading(false);
    }
  }, [agentId]);

  useEffect(() => {
    let isMounted = true;

    async function loadGuardrails() {
      await fetchGuardrails();
    }

    if (isMounted) {
      loadGuardrails();
    }

    return () => {
      isMounted = false;
    };
  }, [agentId, fetchGuardrails]);

  const handleAssign = async (guardrailId: string) => {
    await assignMutation.mutateAsync({ guardrailId, agentId });
    await fetchGuardrails();
  };

  const handleUnassign = async (guardrailId: string) => {
    if (!confirm('Are you sure you want to unassign this guardrail?')) {
      return;
    }

    try {
      await unassignMutation.mutateAsync({ guardrailId, agentId });
      await fetchGuardrails();
    } catch (err) {
      console.error('Failed to unassign guardrail:', err);
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to unassign guardrail. Please try again.'
      );
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-600">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Guardrails</h3>
        <button
          onClick={() => setIsDialogOpen(true)}
          className="px-4 py-2 bg-black text-white rounded-md hover:bg-gray-800 transition-colors text-sm flex items-center gap-2"
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
          Assign Guardrail
        </button>
      </div>

      {/* Guardrails List */}
      {guardrails.length === 0 ? (
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
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
            />
          </svg>
          <h4 className="text-sm font-medium text-gray-900 mb-2">
            No guardrails assigned
          </h4>
          <p className="text-sm text-gray-600 mb-4">
            Assign guardrails to this agent to enforce safety rules
          </p>
          <button
            onClick={() => setIsDialogOpen(true)}
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
            Assign First Guardrail
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {guardrails.map((guardrail) => (
                <tr key={guardrail.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {guardrail.name}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                      Active
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(guardrail.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                    <button
                      onClick={() => handleUnassign(guardrail.id)}
                      disabled={unassignMutation.isPending}
                      className="text-red-600 hover:text-red-900 disabled:opacity-60"
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Assign Guardrail Dialog */}
      <AssignGuardrailDialog
        open={isDialogOpen}
        onOpenChange={setIsDialogOpen}
        agentId={agentId}
        projectId={projectId}
        onAssign={handleAssign}
        assignedGuardrailIds={guardrails.map((g) => g.id)}
      />
    </div>
  );
}
