/**
 * useCreateAgent hook
 *
 * @description TanStack Query hook for creating a new agent.
 * Provides mutation for agent creation with automatic cache invalidation.
 *
 * @module use-create-agent
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { agentService } from '../services';
import type { AgentCreate, Agent } from '../types';

/**
 * useCreateAgent hook
 *
 * @description Creates a mutation hook for agent creation.
 * Automatically invalidates agent list queries on success.
 *
 * **Features**:
 * - Mutation for creating agents
 * - Automatic query invalidation on success
 * - Error handling
 * - Loading state management
 *
 * **Success Behavior**:
 * - Invalidates 'agents' query to refetch agent list
 * - Can be extended with onSuccess callback
 *
 * @returns TanStack Query mutation object
 *
 * @example
 * ```typescript
 * import { useCreateAgent } from '@/features/agents/hooks';
 *
 * function CreateAgentDialog() {
 *   const createMutation = useCreateAgent();
 *
 *   const handleSubmit = (data: AgentCreate) => {
 *     createMutation.mutate(data, {
 *       onSuccess: (agent) => {
 *         console.log('Created:', agent.id);
 *         closeDialog();
 *       },
 *     });
 *   };
 *
 *   return (
 *     <form onSubmit={handleSubmit}>
 *       <input name="name" />
 *       <button disabled={createMutation.isPending}>
 *         {createMutation.isPending ? 'Creating...' : 'Create'}
 *       </button>
 *       {createMutation.error && <p>{createMutation.error.message}</p>}
 *     </form>
 *   );
 * }
 * ```
 */
export function useCreateAgent() {
  const queryClient = useQueryClient();

  return useMutation<Agent, Error, AgentCreate>({
    mutationFn: (data: AgentCreate) => agentService.createAgent(data),
    onSuccess: () => {
      // Invalidate agents query to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });
}
