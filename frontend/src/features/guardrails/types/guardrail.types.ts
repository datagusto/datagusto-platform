/**
 * Guardrail type definitions
 *
 * @description Type definitions for guardrail-related data structures.
 * Maps to backend Pydantic schemas.
 *
 * @module guardrail.types
 */

/**
 * Guardrail response type
 *
 * @description Represents a guardrail entity with all its properties.
 * Matches backend GuardrailResponse schema.
 */
export interface Guardrail {
  id: string;
  project_id: string;
  organization_id: string;
  name: string;
  definition: Record<string, any>;
  created_by: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  is_archived: boolean;
  assigned_agent_count: number;
}

/**
 * Guardrail list response type
 *
 * @description Paginated guardrail list response.
 * Matches backend GuardrailListResponse schema.
 */
export interface GuardrailListResponse {
  items: Guardrail[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Guardrail creation data type
 *
 * @description Data required to create a new guardrail.
 * Matches backend GuardrailCreate schema.
 */
export interface GuardrailCreate {
  name: string;
  definition: Record<string, any>;
  project_id: string;
}

/**
 * Guardrail update data type
 *
 * @description Data for updating a guardrail.
 * Matches backend GuardrailUpdate schema.
 */
export interface GuardrailUpdate {
  name?: string;
  definition?: Record<string, any>;
}
