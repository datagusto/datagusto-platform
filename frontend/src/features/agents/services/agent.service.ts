/**
 * Agent service
 *
 * @description Service for managing agents within a project.
 * Provides methods to fetch, create, update, and delete agents.
 *
 * @module agent.service
 */

import { get, post, patch, del } from '@/shared/lib/api-client';
import type {
  Agent,
  AgentListResponse,
  AgentCreate,
  AgentUpdate,
  AgentAPIKeyCreate,
  AgentAPIKeyCreateResponse,
  AgentAPIKeyListResponse,
} from '../types';

/**
 * Agent service interface
 */
export const agentService = {
  /**
   * Get list of agents in a project
   *
   * @param projectId - Project UUID
   * @param params - Query parameters
   * @returns Promise resolving to paginated agent list
   */
  async listAgents(
    projectId: string,
    params?: {
      page?: number;
      page_size?: number;
      is_active?: boolean;
      is_archived?: boolean;
    }
  ): Promise<AgentListResponse> {
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
      ? `/projects/${projectId}/agents?${query}`
      : `/projects/${projectId}/agents`;

    return get<AgentListResponse>(endpoint);
  },

  /**
   * Get agent details by ID
   *
   * @param agentId - Agent UUID
   * @returns Promise resolving to agent details
   */
  async getAgent(agentId: string): Promise<Agent> {
    return get<Agent>(`/agents/${agentId}`);
  },

  /**
   * Create a new agent
   *
   * @param data - Agent creation data
   * @returns Promise resolving to created agent
   */
  async createAgent(data: AgentCreate): Promise<Agent> {
    return post<Agent>(`/projects/${data.project_id}/agents`, data);
  },

  /**
   * Update agent information
   *
   * @param agentId - Agent UUID
   * @param data - Agent update data
   * @returns Promise resolving to updated agent
   */
  async updateAgent(agentId: string, data: AgentUpdate): Promise<Agent> {
    return patch<Agent>(`/agents/${agentId}`, data);
  },

  /**
   * Archive an agent (soft delete)
   *
   * @param agentId - Agent UUID
   * @param reason - Optional reason for archiving
   * @returns Promise resolving when archive succeeds
   */
  async archiveAgent(agentId: string, reason?: string): Promise<void> {
    return del(`/agents/${agentId}`, {
      body: reason ? JSON.stringify({ reason }) : undefined,
    });
  },

  // API Key management methods

  /**
   * Get list of API keys for an agent
   *
   * @param agentId - Agent UUID
   * @param params - Query parameters
   * @returns Promise resolving to paginated API key list
   */
  async listAPIKeys(
    agentId: string,
    params?: {
      page?: number;
      page_size?: number;
    }
  ): Promise<AgentAPIKeyListResponse> {
    const queryParams = new URLSearchParams();

    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.page_size)
      queryParams.append('page_size', params.page_size.toString());

    const query = queryParams.toString();
    const endpoint = query
      ? `/agents/${agentId}/api-keys?${query}`
      : `/agents/${agentId}/api-keys`;

    return get<AgentAPIKeyListResponse>(endpoint);
  },

  /**
   * Create a new API key for an agent
   *
   * IMPORTANT: The full API key is only returned once in the response.
   * Store it securely - it cannot be retrieved again.
   *
   * @param agentId - Agent UUID
   * @param data - API key creation data
   * @returns Promise resolving to created API key with full key
   */
  async createAPIKey(
    agentId: string,
    data: AgentAPIKeyCreate
  ): Promise<AgentAPIKeyCreateResponse> {
    return post<AgentAPIKeyCreateResponse>(`/agents/${agentId}/api-keys`, data);
  },

  /**
   * Delete an API key
   *
   * @param agentId - Agent UUID
   * @param keyId - API key UUID
   * @returns Promise resolving when delete succeeds
   */
  async deleteAPIKey(agentId: string, keyId: string): Promise<void> {
    return del(`/agents/${agentId}/api-keys/${keyId}`);
  },
};
