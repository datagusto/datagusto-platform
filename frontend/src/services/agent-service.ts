import { apiClient } from "@/lib/api-client";
import type { Agent } from "@/types/agent";

// Endpoints
const API_ENDPOINTS = {
  AGENTS: "/api/v1/agents",
  USER_AGENTS: "/api/v1/users/me/agents",
};

// Agent Service
export const agentService = {
  /**
   * Get all agents for the current user
   */
  getAgents: async (): Promise<Agent[]> => {
    const response = await apiClient.get<Agent[]>(API_ENDPOINTS.USER_AGENTS);

    if (response.error) {
      throw new Error(response.error || 'Failed to fetch agents');
    }

    return response.data;
  },

  /**
   * Get a specific agent by ID
   */
  getAgent: async (agentId: string): Promise<Agent> => {
    const response = await apiClient.get<Agent>(`${API_ENDPOINTS.AGENTS}/${agentId}`);

    if (response.error) {
      throw new Error(response.error || 'Failed to fetch agent');
    }

    return response.data;
  },

  /**
   * Create a new agent
   */
  createAgent: async (agentData: {
    name: string;
    description?: string;
    config?: Record<string, any>;
  }): Promise<Agent & { api_key: string }> => {
    const organizationId = localStorage.getItem('currentOrganizationId');
    if (!organizationId) {
      throw new Error('Organization ID not found');
    }

    const response = await apiClient.post<Agent & { api_key: string }>(
      API_ENDPOINTS.AGENTS,
      agentData,
      { params: { organization_id: organizationId } }
    );

    if (response.error) {
      throw new Error(response.error || 'Failed to create agent');
    }

    return response.data;
  },

  /**
   * Update an existing agent
   */
  updateAgent: async (
    agentId: string,
    agentData: {
      name?: string;
      description?: string;
      status?: string;
      config?: Record<string, any>;
    }
  ): Promise<Agent> => {
    const response = await apiClient.put<Agent>(
      `${API_ENDPOINTS.AGENTS}/${agentId}`,
      agentData
    );

    if (response.error) {
      throw new Error(response.error || 'Failed to update agent');
    }

    return response.data;
  },

  /**
   * Delete an agent
   */
  deleteAgent: async (agentId: string): Promise<void> => {
    const response = await apiClient.delete(`${API_ENDPOINTS.AGENTS}/${agentId}`);

    if (response.error) {
      throw new Error(response.error || 'Failed to delete agent');
    }
  },

  /**
   * Regenerate API key for an agent
   */
  regenerateApiKey: async (agentId: string): Promise<{ api_key: string }> => {
    const response = await apiClient.post<{ api_key: string }>(
      `${API_ENDPOINTS.AGENTS}/${agentId}/regenerate-api-key`
    );

    if (response.error) {
      throw new Error(response.error || 'Failed to regenerate API key');
    }

    return response.data;
  },

  /**
   * Sync traces for an agent
   */
  syncAgent: async (agentId: string): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>(
      `${API_ENDPOINTS.AGENTS}/${agentId}/sync`
    );

    if (response.error) {
      throw new Error(response.error || 'Failed to sync agent traces');
    }

    return response.data;
  }
};

export default agentService; 