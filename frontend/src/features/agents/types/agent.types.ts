/**
 * Agent type definitions
 *
 * @description Type definitions for agent-related data structures.
 * Maps to backend Pydantic schemas.
 *
 * @module agent.types
 */

/**
 * Agent response type
 *
 * @description Represents an agent entity with all its properties.
 * Matches backend AgentResponse schema.
 */
export interface Agent {
  id: string;
  project_id: string;
  organization_id: string;
  name: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  is_archived: boolean;
  api_key_count: number;
}

/**
 * Agent list response type
 *
 * @description Paginated agent list response.
 * Matches backend AgentListResponse schema.
 */
export interface AgentListResponse {
  items: Agent[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Agent creation data type
 *
 * @description Data required to create a new agent.
 * Matches backend AgentCreate schema.
 */
export interface AgentCreate {
  name: string;
  project_id: string;
}

/**
 * Agent update data type
 *
 * @description Data for updating an agent.
 * Matches backend AgentUpdate schema.
 */
export interface AgentUpdate {
  name?: string;
}
