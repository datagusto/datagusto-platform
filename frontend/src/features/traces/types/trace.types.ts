/**
 * Trace type definitions
 *
 * @description Type definitions for trace-related data structures.
 * Maps to backend Pydantic schemas.
 *
 * @module trace.types
 */

/**
 * Trace response type
 *
 * @description Represents a trace entity with all its properties.
 * Matches backend TraceResponse schema.
 */
export interface Trace {
  id: string;
  agent_id: string;
  project_id: string;
  organization_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'error';
  started_at: string;
  ended_at: string | null;
  trace_metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  observation_count: number;
}

/**
 * Trace list response type
 *
 * @description Paginated trace list response.
 * Matches backend TraceListResponse schema.
 */
export interface TraceListResponse {
  items: Trace[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Trace creation data type
 *
 * @description Data required to create a new trace.
 * Matches backend TraceCreate schema.
 */
export interface TraceCreate {
  agent_id: string;
  status?: string;
  started_at?: string;
  trace_metadata?: Record<string, any>;
}

/**
 * Trace update data type
 *
 * @description Data for updating a trace.
 * Matches backend TraceUpdate schema.
 */
export interface TraceUpdate {
  status?: string;
  ended_at?: string;
  trace_metadata?: Record<string, any>;
}
