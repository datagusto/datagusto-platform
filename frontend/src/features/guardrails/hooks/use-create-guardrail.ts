/**
 * Create guardrail hook
 *
 * @description React Query mutation hook for creating guardrails.
 * Handles API call, loading state, and error handling.
 *
 * @module use-create-guardrail
 */

'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { guardrailService } from '../services';
import type { GuardrailCreate } from '../types';

/**
 * Hook for creating a new guardrail
 *
 * @description Provides mutation for guardrail creation with automatic
 * cache invalidation on success.
 *
 * @returns Mutation object with mutate function and state
 *
 * @example
 * ```tsx
 * const createGuardrail = useCreateGuardrail();
 *
 * const handleSubmit = (data) => {
 *   createGuardrail.mutate({
 *     project_id: projectId,
 *     name: data.name,
 *     definition: data.definition,
 *   }, {
 *     onSuccess: (guardrail) => {
 *       console.log('Created:', guardrail);
 *       router.push(`/projects/${projectId}/guardrails`);
 *     },
 *   });
 * };
 * ```
 */
export function useCreateGuardrail() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: GuardrailCreate) =>
      guardrailService.createGuardrail(data),
    onSuccess: (data, variables) => {
      // Invalidate guardrails list for this project
      queryClient.invalidateQueries({
        queryKey: ['guardrails', variables.project_id],
      });

      // Optionally set the created guardrail in cache
      queryClient.setQueryData(['guardrail', data.id], data);
    },
  });
}
