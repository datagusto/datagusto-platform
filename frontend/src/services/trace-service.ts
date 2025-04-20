import { apiClient } from "@/lib/api-client";
import type { Trace, Observation } from "@/types";

// Endpoints
const API_ENDPOINTS = {
  TRACES: "/api/v1/traces",
  AGENT_TRACES: (agentId: string) => `/api/v1/agents/${agentId}/traces`,
};

// Trace Service
export const traceService = {
  /**
   * Get all traces for the current user
   */
  getTraces: async (): Promise<Trace[]> => {
    const response = await apiClient.get<Trace[]>(API_ENDPOINTS.TRACES);

    if (response.error) {
      throw new Error(response.error || 'Failed to fetch traces');
    }

    return response.data;
  },

  /**
   * Get traces for a specific agent
   */
  getAgentTraces: async (agentId: string): Promise<Trace[]> => {
    const response = await apiClient.get<Trace[]>(API_ENDPOINTS.AGENT_TRACES(agentId));

    if (response.error) {
      throw new Error(response.error || 'Failed to fetch agent traces');
    }

    return response.data;
  },

  /**
   * Get a specific trace by ID
   */
  getTrace: async (traceId: string): Promise<Trace> => {
    const response = await apiClient.get<Trace>(`${API_ENDPOINTS.TRACES}/${traceId}`);

    if (response.error) {
      throw new Error(response.error || 'Failed to fetch trace');
    }

    return response.data;
  },

  /**
   * Get only observations for a specific trace
   */
  getTraceObservations: async (traceId: string): Promise<Observation[]> => {
    const response = await apiClient.get<Observation[]>(
      `${API_ENDPOINTS.TRACES}/${traceId}/observations`
    );

    if (response.error) {
      throw new Error(response.error || 'Failed to fetch trace observations');
    }

    return response.data;
  },

  /**
   * Add an observation to a trace
   */
  addObservation: async (
    traceId: string,
    observationData: {
      type: string;
      name: string;
      input?: any;
      output?: any;
      parentObservationId?: string;
    }
  ): Promise<Observation> => {
    const response = await apiClient.post<Observation>(
      `${API_ENDPOINTS.TRACES}/${traceId}/observations`,
      observationData
    );

    if (response.error) {
      throw new Error(response.error || 'Failed to add observation');
    }

    return response.data;
  }
};

export default traceService; 