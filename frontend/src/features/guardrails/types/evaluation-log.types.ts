/**
 * Guardrail evaluation log type definitions
 *
 * @description Types for guardrail evaluation logs from the API.
 * Maps to backend GuardrailEvaluationLog model.
 *
 * @module evaluation-log.types
 */

/**
 * Triggered guardrail information
 */
export interface TriggeredGuardrail {
  guardrail_id: string;
  guardrail_name: string;
  triggered: boolean;
  ignored: boolean;
  ignored_reason?: string;
  error: boolean;
  error_message?: string;
  matched_conditions: number[];
  actions: ActionResult[];
}

/**
 * Action result from evaluation
 */
export interface ActionResult {
  action_type: 'block' | 'warn' | 'modify';
  priority: number;
  result: Record<string, unknown>;
}

/**
 * Evaluation metadata
 */
export interface EvaluationMetadata {
  evaluation_time_ms: number;
  evaluated_guardrails_count: number;
  triggered_guardrails_count: number;
  ignored_guardrails_count: number;
}

/**
 * Guardrail evaluation log
 */
export interface GuardrailEvaluationLog {
  id: string;
  request_id: string;
  agent_id: string;
  project_id: string;
  organization_id: string;
  trace_id?: string;
  timing: 'on_start' | 'on_end';
  process_type: 'llm' | 'tool' | 'retrieval' | 'agent';
  should_proceed: boolean;
  log_data: {
    process_name: string;
    request_context: Record<string, unknown>;
    evaluated_guardrail_ids: string[];
    triggered_guardrail_ids: string[];
    evaluation_result: {
      triggered_guardrails: TriggeredGuardrail[];
      metadata: EvaluationMetadata;
    };
    evaluation_time_ms: number;
  };
  created_at: string;
  updated_at: string;
}

/**
 * Evaluation logs list response
 */
export interface EvaluationLogsListResponse {
  items: GuardrailEvaluationLog[];
  total: number;
  page: number;
  page_size: number;
}
