/**
 * useUnassignGuardrail hook
 *
 * @description React Query hook for unassigning a guardrail from an agent.
 * Provides mutation with automatic cache invalidation.
 *
 * @module use-unassign-guardrail
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { guardrailService } from '@/features/guardrails/services';

/**
 * Unassignment parameters
 */
interface UnassignGuardrailParams {
  guardrailId: string;
  agentId: string;
}

/**
 * useUnassignGuardrail hook
 *
 * @description Creates a mutation hook for unassigning guardrails from agents.
 * Automatically invalidates agent guardrails queries on success.
 *
 * @returns TanStack Query mutation object
 *
 * @example
 * ```typescript
 * const unassignMutation = useUnassignGuardrail();
 *
 * const handleUnassign = (guardrailId: string, agentId: string) => {
 *   unassignMutation.mutate(
 *     { guardrailId, agentId },
 *     {
 *       onSuccess: () => {
 *         console.log('Guardrail unassigned successfully');
 *       },
 *     }
 *   );
 * };
 * ```
 */
export function useUnassignGuardrail() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, UnassignGuardrailParams>({
    mutationFn: ({ guardrailId, agentId }: UnassignGuardrailParams) =>
      guardrailService.unassignFromAgent(guardrailId, agentId),
    onSuccess: (_, variables) => {
      // Invalidate agent guardrails query to trigger refetch
      queryClient.invalidateQueries({
        queryKey: ['guardrails', 'agent', variables.agentId],
      });
    },
  });
}
