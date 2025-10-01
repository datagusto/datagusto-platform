/**
 * Assign guardrail dialog component
 *
 * @description Dialog for assigning a guardrail to an agent.
 * Shows list of available guardrails in the project.
 *
 * @module assign-guardrail-dialog
 */

'use client';

import { useState, useEffect } from 'react';
import { guardrailService } from '@/features/guardrails/services';
import type { Guardrail } from '@/features/guardrails/types';

/**
 * Assign guardrail dialog props
 */
interface AssignGuardrailDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agentId: string;
  projectId: string;
  onAssign: (guardrailId: string) => Promise<void>;
  assignedGuardrailIds: string[];
}

/**
 * Assign guardrail dialog component
 *
 * @description Displays available guardrails and allows selection for assignment.
 */
export function AssignGuardrailDialog({
  open,
  onOpenChange,
  agentId,
  projectId,
  onAssign,
  assignedGuardrailIds,
}: AssignGuardrailDialogProps) {
  const [guardrails, setGuardrails] = useState<Guardrail[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [selectedGuardrailId, setSelectedGuardrailId] = useState<string | null>(null);

  // Fetch available guardrails when dialog opens
  useEffect(() => {
    if (!open) return;

    let isMounted = true;

    async function fetchGuardrails() {
      try {
        setIsFetching(true);
        setError(null);

        const response = await guardrailService.listGuardrails(projectId, {
          is_active: true,
          is_archived: false,
        });

        if (!isMounted) return;

        // Filter out already assigned guardrails
        const available = response.items.filter(
          (g) => !assignedGuardrailIds.includes(g.id)
        );
        setGuardrails(available);
      } catch (err) {
        if (!isMounted) return;
        setError(err instanceof Error ? err : new Error('Failed to load guardrails'));
      } finally {
        if (isMounted) {
          setIsFetching(false);
        }
      }
    }

    fetchGuardrails();

    return () => {
      isMounted = false;
    };
  }, [open, projectId, assignedGuardrailIds]);

  const handleAssign = async () => {
    if (!selectedGuardrailId) return;

    try {
      setIsLoading(true);
      setError(null);
      await onAssign(selectedGuardrailId);
      handleClose();
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to assign guardrail'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      onOpenChange(false);
      setTimeout(() => {
        setSelectedGuardrailId(null);
        setError(null);
        setGuardrails([]);
      }, 300);
    }
  };

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-50"
        onClick={handleClose}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
        <div
          className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[80vh] flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="p-6 border-b">
            <h2 className="text-xl font-bold text-gray-900">
              Assign Guardrail
            </h2>
            <p className="mt-1 text-sm text-gray-600">
              Select a guardrail to assign to this agent
            </p>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {isFetching ? (
              <div className="flex justify-center items-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
              </div>
            ) : error ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-600">
                {error.message}
              </div>
            ) : guardrails.length === 0 ? (
              <div className="text-center py-12">
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
                  No available guardrails
                </h4>
                <p className="text-sm text-gray-600">
                  All guardrails in this project are already assigned to this agent
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {guardrails.map((guardrail) => (
                  <button
                    key={guardrail.id}
                    type="button"
                    onClick={() => setSelectedGuardrailId(guardrail.id)}
                    className={`w-full text-left p-4 border rounded-lg transition-colors ${
                      selectedGuardrailId === guardrail.id
                        ? 'border-black bg-gray-50'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">
                          {guardrail.name}
                        </h4>
                        <p className="text-xs text-gray-500 mt-1">
                          Created {new Date(guardrail.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      {selectedGuardrailId === guardrail.id && (
                        <svg
                          className="w-5 h-5 text-black flex-shrink-0"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-6 border-t bg-gray-50 flex gap-3">
            <button
              type="button"
              onClick={handleClose}
              disabled={isLoading}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-100 transition-colors disabled:opacity-60"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleAssign}
              disabled={!selectedGuardrailId || isLoading}
              className="flex-1 px-4 py-2 bg-black text-white rounded-md hover:bg-gray-800 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Assigning...' : 'Assign'}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
