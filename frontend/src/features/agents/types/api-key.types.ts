/**
 * Agent API Key types
 *
 * @description Type definitions for agent API key management.
 *
 * @module api-key.types
 */

/**
 * Agent API Key
 *
 * @description Represents an API key for agent authentication.
 * The full API key is never stored or returned after creation.
 */
export interface AgentAPIKey {
  id: string;
  agent_id: string;
  key_prefix: string;
  name: string | null;
  last_used_at: string | null;
  expires_at: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
  is_expired: boolean;
}

/**
 * Agent API Key creation response
 *
 * @description Response from creating a new API key.
 * IMPORTANT: The `api_key` field is only returned once.
 */
export interface AgentAPIKeyCreateResponse extends AgentAPIKey {
  api_key: string;
}

/**
 * Agent API Key creation request
 *
 * @description Data required to create a new API key.
 */
export interface AgentAPIKeyCreate {
  name?: string;
  expires_in_days?: number;
}

/**
 * Agent API Key list response
 *
 * @description Paginated list of API keys.
 */
export interface AgentAPIKeyListResponse {
  items: AgentAPIKey[];
  total: number;
  page: number;
  page_size: number;
}
