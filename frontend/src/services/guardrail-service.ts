import { apiClient, MockApiClient } from "@/lib/api-client";
import { guardrailActions as mockGuardrailActions } from "@/data/guardrails";

// Types
export interface Guardrail {
  id: number;
  name: string;
  validation: string;
  condition: string;
  action: string;
  status: string;
  description: string;
}

export interface GuardrailAction {
  id: number;
  name: string;
  description: string;
}

// Mock data for development
const initialGuardrails = [
  {
    id: 3,
    name: "Content Safety Filter",
    validation: "Toxic Content Detection",
    condition: "Contains Toxic Content",
    action: "Stop Processing",
    status: "Active",
    description: "Detects toxic content in outputs and stops processing, directing to support"
  }
];

// Endpoints
const API_ENDPOINTS = {
  BASE: "/api/v1/guardrails",
  AGENT_GUARDRAILS: (agentId: string) => `/api/v1/agents/${agentId}/guardrails`
};

// Mock client setup
const createMockGuardrailClient = () => {
  return new MockApiClient<Guardrail[]>({
    getData: () => [...initialGuardrails],
    
    find: (id: string) => {
      const guardrail = initialGuardrails.find(g => g.id.toString() === id);
      if (!guardrail) {
        throw new Error("Guardrail not found");
      }
      return guardrail;
    },
    
    create: (guardrailData: Omit<Guardrail, "id">) => {
      const newGuardrail: Guardrail = {
        id: initialGuardrails.length > 0 
          ? Math.max(...initialGuardrails.map(g => g.id)) + 1 
          : 1,
        ...guardrailData
      };
      
      initialGuardrails.push(newGuardrail);
      return newGuardrail;
    },
    
    update: (id: string, guardrailData: Partial<Guardrail>) => {
      const guardrailIndex = initialGuardrails.findIndex(g => g.id.toString() === id);
      
      if (guardrailIndex === -1) {
        throw new Error("Guardrail not found");
      }
      
      initialGuardrails[guardrailIndex] = {
        ...initialGuardrails[guardrailIndex],
        ...guardrailData
      };
      
      return initialGuardrails[guardrailIndex];
    },
    
    delete: (id: string) => {
      const guardrailIndex = initialGuardrails.findIndex(g => g.id.toString() === id);
      
      if (guardrailIndex === -1) {
        throw new Error("Guardrail not found");
      }
      
      initialGuardrails.splice(guardrailIndex, 1);
    }
  });
};

// Determine if we should use mock or real API
const shouldUseMock = () => !process.env.NEXT_PUBLIC_API_URL;
const mockGuardrailClient = createMockGuardrailClient();

// Guardrail Service
export const guardrailService = {
  /**
   * Get all guardrails
   */
  getGuardrails: async (): Promise<Guardrail[]> => {
    if (shouldUseMock()) {
      console.warn('API URL not configured, using mock data for guardrails');
      return mockGuardrailClient.get();
    }
    
    const response = await apiClient.get<Guardrail[]>(API_ENDPOINTS.BASE);
    
    if (response.error) {
      throw new Error(response.error || 'Failed to fetch guardrails');
    }
    
    return response.data;
  },
  
  /**
   * Get guardrails for a specific agent
   */
  getAgentGuardrails: async (agentId: string): Promise<Guardrail[]> => {
    if (shouldUseMock()) {
      console.warn('API URL not configured, using mock data for agent guardrails');
      return mockGuardrailClient.get();
    }
    
    const response = await apiClient.get<Guardrail[]>(API_ENDPOINTS.AGENT_GUARDRAILS(agentId));
    
    if (response.error) {
      throw new Error(response.error || 'Failed to fetch agent guardrails');
    }
    
    return response.data;
  },
  
  /**
   * Create a new guardrail
   */
  createGuardrail: async (guardrailData: Omit<Guardrail, "id">): Promise<Guardrail> => {
    if (shouldUseMock()) {
      console.warn('API URL not configured, using mock implementation for creating guardrail');
      return mockGuardrailClient.create(guardrailData);
    }
    
    const response = await apiClient.post<Guardrail>(API_ENDPOINTS.BASE, guardrailData);
    
    if (response.error) {
      throw new Error(response.error || 'Failed to create guardrail');
    }
    
    return response.data;
  },
  
  /**
   * Update a guardrail
   */
  updateGuardrail: async (guardrailId: number, guardrailData: Partial<Guardrail>): Promise<Guardrail> => {
    if (shouldUseMock()) {
      console.warn('API URL not configured, using mock implementation for updating guardrail');
      return mockGuardrailClient.update(guardrailId.toString(), guardrailData);
    }
    
    const response = await apiClient.put<Guardrail>(
      `${API_ENDPOINTS.BASE}/${guardrailId}`,
      guardrailData
    );
    
    if (response.error) {
      throw new Error(response.error || 'Failed to update guardrail');
    }
    
    return response.data;
  },
  
  /**
   * Delete a guardrail
   */
  deleteGuardrail: async (guardrailId: number): Promise<void> => {
    if (shouldUseMock()) {
      console.warn('API URL not configured, using mock implementation for deleting guardrail');
      return mockGuardrailClient.delete(guardrailId.toString());
    }
    
    const response = await apiClient.delete(`${API_ENDPOINTS.BASE}/${guardrailId}`);
    
    if (response.error) {
      throw new Error(response.error || 'Failed to delete guardrail');
    }
  },
  
  /**
   * Get available guardrail actions
   */
  getGuardrailActions: async (): Promise<GuardrailAction[]> => {
    if (shouldUseMock()) {
      console.warn('API URL not configured, using mock data for guardrail actions');
      return Promise.resolve(mockGuardrailActions);
    }
    
    const response = await apiClient.get<GuardrailAction[]>(`${API_ENDPOINTS.BASE}/actions`);
    
    if (response.error) {
      throw new Error(response.error || 'Failed to fetch guardrail actions');
    }
    
    return response.data;
  }
};

export default guardrailService; 