import { MOCK_AGENTS } from "./mock";
import type { Agent } from "@/types/agent";
import { fetchOrganizationId, isAuthenticated } from "@/utils/auth";

// JWTトークンを取得する関数
function getAccessToken(): string | null {
  try {
    const token = localStorage.getItem('access_token');
    if (!token) {
      return null;
    }
    return token;
  } catch (error) {
    console.error('Error getting access token:', error);
    return null;
  }
}

// 組織IDを取得する関数（ローカルストレージからのみ）
function getOrganizationId(): string | null {
  try {
    return localStorage.getItem('currentOrganizationId');
  } catch (error) {
    console.error('Error getting organization ID from localStorage:', error);
    return null;
  }
}

// ログイン時に既に取得されているはずの組織IDを確認する関数
function ensureOrganizationId(): string {
  // 認証されていない場合はエラー
  if (!isAuthenticated()) {
    throw new Error('Authentication required');
  }
  
  const organizationId = getOrganizationId();
  if (!organizationId) {
    // この時点で組織IDがない場合は、認証情報が壊れている可能性がある
    throw new Error('Organization ID not found. Please log out and log in again.');
  }
  
  return organizationId;
}

export async function getAgents(): Promise<Agent[]> {
  // Check if API URL is defined
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  
  // Use mock data if no API URL is configured
  if (!apiUrl) {
    console.warn('API URL not configured, using mock data');
    return Promise.resolve(MOCK_AGENTS);
  }
  
  try {
    const accessToken = getAccessToken();
    if (!accessToken) {
      throw new Error('Authentication required');
    }

    const response = await fetch(
      `${apiUrl}/api/v1/users/me/agents`,
      {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch agents');
    }

    return response.json();
  } catch (error) {
    console.error('Error fetching agents:', error);
    // Fall back to mock data in case of error
    return MOCK_AGENTS;
  }
}

export async function getAgent(agentId: string): Promise<Agent> {
  // Check if API URL is defined
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  
  // Use mock data if no API URL is configured
  if (!apiUrl) {
    console.warn('API URL not configured, using mock data');
    const mockAgent = MOCK_AGENTS.find((a: Agent) => a.id === agentId);
    if (!mockAgent) {
      throw new Error('Agent not found');
    }
    return Promise.resolve(mockAgent);
  }
  
  try {
    const accessToken = getAccessToken();
    if (!accessToken) {
      throw new Error('Authentication required');
    }

    const response = await fetch(
      `${apiUrl}/api/v1/agents/${agentId}`,
      {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch agent');
    }

    return response.json();
  } catch (error) {
    console.error('Error fetching agent:', error);
    // Check if we can find a mock agent with this ID
    const mockAgent = MOCK_AGENTS.find((a: Agent) => a.id === agentId);
    if (mockAgent) {
      return mockAgent;
    }
    throw error;
  }
}

export async function createAgent(agentData: {
  name: string;
  description?: string;
  config?: Record<string, any>;
}): Promise<Agent & { api_key: string }> {
  // ログイン後に取得済みのはずの組織IDを使用
  const organizationId = ensureOrganizationId();

  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) {
    console.warn('API URL not configured, using mock implementation');
    // Create a mock agent with a unique ID
    const newId = (Math.max(...MOCK_AGENTS.map((a: Agent) => Number(a.id))) + 1).toString();
    const newAgent = {
      id: newId,
      organization_id: organizationId,
      name: agentData.name,
      description: agentData.description || null,
      status: "ACTIVE",
      config: agentData.config || null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      api_key: `sk-mock-${newId}-${Math.random().toString(36).substring(2, 10)}`
    };
    
    MOCK_AGENTS.push(newAgent);
    return Promise.resolve(newAgent);
  }

  const accessToken = getAccessToken();
  if (!accessToken) {
    throw new Error('Authentication required');
  }

  const response = await fetch(
    `${apiUrl}/api/v1/agents?organization_id=${organizationId}`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(agentData),
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to create agent');
  }

  return response.json();
}

export async function updateAgent(agentId: string, agentData: {
  name?: string;
  description?: string;
  status?: string;
  config?: Record<string, any>;
}): Promise<Agent> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) {
    console.warn('API URL not configured, using mock implementation');
    const agentIndex = MOCK_AGENTS.findIndex((a: Agent) => a.id === agentId);
    if (agentIndex === -1) {
      throw new Error('Agent not found');
    }
    
    // Update the mock agent
    MOCK_AGENTS[agentIndex] = {
      ...MOCK_AGENTS[agentIndex],
      ...agentData,
      updated_at: new Date().toISOString()
    };
    
    return Promise.resolve(MOCK_AGENTS[agentIndex]);
  }

  const accessToken = getAccessToken();
  if (!accessToken) {
    throw new Error('Authentication required');
  }

  const response = await fetch(
    `${apiUrl}/api/v1/agents/${agentId}`,
    {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(agentData),
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to update agent');
  }

  return response.json();
}

export async function deleteAgent(agentId: string): Promise<void> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) {
    console.warn('API URL not configured, using mock implementation');
    const agentIndex = MOCK_AGENTS.findIndex((a: Agent) => a.id === agentId);
    if (agentIndex === -1) {
      throw new Error('Agent not found');
    }
    
    // Remove the agent from the mock data
    MOCK_AGENTS.splice(agentIndex, 1);
    return Promise.resolve();
  }

  const accessToken = getAccessToken();
  if (!accessToken) {
    throw new Error('Authentication required');
  }

  const response = await fetch(
    `${apiUrl}/api/v1/agents/${agentId}`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to delete agent');
  }
}

export async function regenerateApiKey(agentId: string): Promise<{ api_key: string }> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) {
    console.warn('API URL not configured, using mock implementation');
    const agent = MOCK_AGENTS.find((a: Agent) => a.id === agentId);
    if (!agent) {
      throw new Error('Agent not found');
    }
    
    // Generate a mock API key
    const apiKey = `sk-mock-${agentId}-${Math.random().toString(36).substring(2, 10)}`;
    return Promise.resolve({ api_key: apiKey });
  }

  const accessToken = getAccessToken();
  if (!accessToken) {
    throw new Error('Authentication required');
  }

  const response = await fetch(
    `${apiUrl}/api/v1/agents/${agentId}/regenerate-api-key`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to regenerate API key');
  }

  return response.json();
} 