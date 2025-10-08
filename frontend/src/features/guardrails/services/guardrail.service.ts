/**
 * Guardrail service
 *
 * @description Service for managing guardrails within a project.
 * Provides methods to fetch, create, update, and delete guardrails.
 *
 * @module guardrail.service
 */

import { get, post, patch, del } from '@/shared/lib/api-client';
import type {
  Guardrail,
  GuardrailListResponse,
  GuardrailCreate,
  GuardrailUpdate,
} from '../types';

/**
 * Guardrail service interface
 */
export const guardrailService = {
  /**
   * Get list of guardrails in a project
   *
   * @param projectId - Project UUID
   * @param params - Query parameters
   * @returns Promise resolving to paginated guardrail list
   */
  async listGuardrails(
    projectId: string,
    params?: {
      page?: number;
      page_size?: number;
      is_active?: boolean;
      is_archived?: boolean;
    }
  ): Promise<GuardrailListResponse> {
    const queryParams = new URLSearchParams();

    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.page_size)
      queryParams.append('page_size', params.page_size.toString());
    if (params?.is_active !== undefined)
      queryParams.append('is_active', params.is_active.toString());
    if (params?.is_archived !== undefined)
      queryParams.append('is_archived', params.is_archived.toString());

    const query = queryParams.toString();
    const endpoint = query
      ? `/projects/${projectId}/guardrails?${query}`
      : `/projects/${projectId}/guardrails`;

    return get<GuardrailListResponse>(endpoint);
  },

  /**
   * Get guardrail details by ID
   *
   * @param guardrailId - Guardrail UUID
   * @returns Promise resolving to guardrail details
   */
  async getGuardrail(guardrailId: string): Promise<Guardrail> {
    return get<Guardrail>(`/guardrails/${guardrailId}`);
  },

  /**
   * Create a new guardrail
   *
   * @param data - Guardrail creation data
   * @returns Promise resolving to created guardrail
   */
  async createGuardrail(data: GuardrailCreate): Promise<Guardrail> {
    return post<Guardrail>(`/projects/${data.project_id}/guardrails`, data);
  },

  /**
   * Update guardrail information
   *
   * @param guardrailId - Guardrail UUID
   * @param data - Guardrail update data
   * @returns Promise resolving to updated guardrail
   */
  async updateGuardrail(
    guardrailId: string,
    data: GuardrailUpdate
  ): Promise<Guardrail> {
    return patch<Guardrail>(`/guardrails/${guardrailId}`, data);
  },

  /**
   * Archive a guardrail (soft delete)
   *
   * @param guardrailId - Guardrail UUID
   * @param reason - Optional reason for archiving
   * @returns Promise resolving when archive succeeds
   */
  async archiveGuardrail(guardrailId: string, reason?: string): Promise<void> {
    return del(`/guardrails/${guardrailId}`, {
      body: reason ? JSON.stringify({ reason }) : undefined,
    });
  },

  /**
   * Assign guardrail to an agent
   *
   * @param guardrailId - Guardrail UUID
   * @param agentId - Agent UUID
   * @returns Promise resolving to assignment record
   */
  async assignToAgent(
    guardrailId: string,
    agentId: string
  ): Promise<{
    id: string;
    guardrail_id: string;
    agent_id: string;
    assigned_by: string;
    created_at: string;
  }> {
    return post(`/guardrails/${guardrailId}/assignments`, {
      agent_id: agentId,
    });
  },

  /**
   * Unassign guardrail from an agent
   *
   * @param guardrailId - Guardrail UUID
   * @param agentId - Agent UUID
   * @returns Promise resolving when unassignment succeeds
   */
  async unassignFromAgent(guardrailId: string, agentId: string): Promise<void> {
    return del(`/guardrails/${guardrailId}/assignments/${agentId}`);
  },
};
