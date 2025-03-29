import type { Agent } from "@/types/agent";

// Mock data for development environment
export const MOCK_AGENTS: Agent[] = [
  {
    id: "1",
    organization_id: "org1",
    name: "Customer Support Agent",
    description: "Handles customer inquiries and support tickets",
    status: "ACTIVE",
    config: { model: "gpt-4", temperature: 0.7 },
    created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString()
  },
  {
    id: "2",
    organization_id: "org1",
    name: "Data Analysis Agent",
    description: "Processes and analyzes business data",
    status: "INACTIVE",
    config: { model: "gpt-3.5-turbo", temperature: 0.3 },
    created_at: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString()
  }
]; 