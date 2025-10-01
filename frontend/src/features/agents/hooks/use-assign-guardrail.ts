/**
 * useAssignGuardrail hook
 *
 * @description React Query hook for assigning a guardrail to an agent.
 * Provides mutation with automatic cache invalidation.
 *
 * @module use-assign-guardrail
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { guardrailService } from '@/features/guardrails/services';

/**
 * Assignment parameters
 */
interface AssignGuardrailParams {
  guardrailId: string;
  agentId: string;
}

/**
 * Assignment response
 */
interface AssignmentResponse {
  id: string;
  guardrail_id: string;
  agent_id: string;
  assigned_by: string;
  created_at: string;
}

/**
 * useAssignGuardrail hook
 *
 * @description Creates a mutation hook for assigning guardrails to agents.
 * Automatically invalidates agent guardrails queries on success.
 *
 * @returns TanStack Query mutation object
 *
 * @example
 * ```typescript
 * const assignMutation = useAssignGuardrail();
 *
 * const handleAssign = (guardrailId: string, agentId: string) => {
 *   assignMutation.mutate(
 *     { guardrailId, agentId },
 *     {
 *       onSuccess: () => {
 *         console.log('Guardrail assigned successfully');
 *       },
 *     }
 *   );
 * };
 * ```
 */
export function useAssignGuardrail() {
  const queryClient = useQueryClient();

  return useMutation<AssignmentResponse, Error, AssignGuardrailParams>({
    mutationFn: ({ guardrailId, agentId }: AssignGuardrailParams) =>
      guardrailService.assignToAgent(guardrailId, agentId),
    onSuccess: (_, variables) => {
      // Invalidate agent guardrails query to trigger refetch
      queryClient.invalidateQueries({
        queryKey: ['guardrails', 'agent', variables.agentId],
      });
    },
  });
}
