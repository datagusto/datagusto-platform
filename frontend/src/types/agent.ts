export interface Agent {
  id: string;
  organization_id: string;
  name: string;
  description: string | null;
  status: string;
  config: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface AgentWithApiKey extends Agent {
  api_key: string;
}

export interface AgentCreate {
  name: string;
  description?: string;
  config?: Record<string, any>;
} 