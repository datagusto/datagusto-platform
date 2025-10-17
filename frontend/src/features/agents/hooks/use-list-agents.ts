/**
 * useListAgents hook
 *
 * @description TanStack Query hook for fetching agent list.
 * Provides query for agent list with automatic caching and refetching.
 *
 * @module use-list-agents
 */

import { useQuery } from '@tanstack/react-query';
import { agentService } from '../services';
import type { AgentListResponse } from '../types';

/**
 * List agents query parameters
 *
 * @property {number} [page] - Page number (1-indexed)
 * @property {number} [page_size] - Number of items per page
 * @property {boolean} [is_active] - Filter by active status
 * @property {boolean} [is_archived] - Filter by archived status
 */
interface ListAgentsParams {
  page?: number;
  page_size?: number;
  is_active?: boolean;
  is_archived?: boolean;
}

/**
 * useListAgents hook
 *
 * @description Creates a query hook for fetching agent list.
 * Automatically caches results and refetches on invalidation.
 *
 * **Features**:
 * - Query for fetching agents
 * - Automatic caching with React Query
 * - Automatic refetch on cache invalidation
 * - Loading and error states
 * - Enabled/disabled query control
 *
 * **Query Key Structure**:
 * - `['agents', projectId, params]` - For parameterized queries
 * - Allows targeted invalidation by project
 *
 * @param projectId - Project UUID
 * @param params - Query parameters for filtering and pagination
 * @param options - Additional query options
 * @returns TanStack Query query object
 *
 * @example
 * ```typescript
 * import { useListAgents } from '@/features/agents/hooks';
 *
 * function AgentList({ projectId }: { projectId: string }) {
 *   const { data, isLoading, error, refetch } = useListAgents(projectId, {
 *     is_active: true,
 *     is_archived: false,
 *   });
 *
 *   if (isLoading) return <div>Loading...</div>;
 *   if (error) return <div>Error: {error.message}</div>;
 *
 *   return (
 *     <div>
 *       <h2>Agents ({data?.total})</h2>
 *       {data?.items.map(agent => (
 *         <div key={agent.id}>{agent.name}</div>
 *       ))}
 *       <button onClick={() => refetch()}>Refresh</button>
 *     </div>
 *   );
 * }
 * ```
 *
 * @example
 * ```typescript
 * // Conditional query - only fetch when projectId is available
 * const { data } = useListAgents(projectId, {}, { enabled: !!projectId });
 * ```
 */
export function useListAgents(
  projectId: string,
  params?: ListAgentsParams,
  options?: {
    enabled?: boolean;
  }
) {
  return useQuery<AgentListResponse, Error>({
    queryKey: ['agents', projectId, params],
    queryFn: () => agentService.listAgents(projectId, params),
    enabled: options?.enabled !== false && !!projectId,
  });
}
