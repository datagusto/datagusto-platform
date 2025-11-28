/**
 * Alignment session types
 *
 * @description Type definitions for alignment sessions and validation history.
 *
 * @module types/alignment
 */

/**
 * Alignment session list item
 *
 * @description Represents a single alignment session in the list view.
 */
export interface AlignmentSession {
  /**
   * Unique session identifier (UUID)
   */
  session_id: string;

  /**
   * Original user instruction text
   */
  user_instruction: string;

  /**
   * Number of ambiguous terms requiring clarification
   */
  ambiguous_terms_count: number;

  /**
   * Number of resolved terms
   */
  resolved_terms_count: number;

  /**
   * Number of validation rules generated
   */
  validation_rules_count: number;

  /**
   * Number of validation history entries
   */
  validation_history_count: number;

  /**
   * Whether session has any invalid validations
   */
  has_invalid_validations: boolean;

  /**
   * Session creation timestamp (ISO 8601)
   */
  created_at: string;

  /**
   * Last update timestamp (ISO 8601)
   */
  updated_at: string;
}

/**
 * Alignment session list response
 *
 * @description Response from the session list endpoint.
 */
export interface AlignmentSessionListResponse {
  /**
   * List of sessions
   */
  sessions: AlignmentSession[];

  /**
   * Total number of sessions
   */
  total: number;
}

/**
 * Term extracted from user instruction
 */
export interface Term {
  /**
   * The extracted term
   */
  term: string;

  /**
   * Category of the term (e.g., time, location, object, action)
   */
  category: string;
}

/**
 * Resolved term with interpretation
 */
export interface ResolvedTerm {
  /**
   * The extracted term
   */
  term: string;

  /**
   * Category of the term
   */
  category: string;

  /**
   * The specific interpretation or concrete value
   */
  resolved_value: string;

  /**
   * Confidence level (HIGH, MEDIUM, LOW)
   */
  confidence: string;
}

/**
 * Guardrail condition
 */
export interface GuardrailCondition {
  /**
   * Field to check (input/output)
   */
  field: string;

  /**
   * Operator (llm_judge, etc.)
   */
  operator: string;

  /**
   * Value/prompt for evaluation
   */
  value: string;
}

/**
 * Guardrail trigger
 */
export interface GuardrailTrigger {
  /**
   * Trigger type (on_start/on_end)
   */
  type: string;

  /**
   * Logic operator (and/or)
   */
  logic: string;

  /**
   * Trigger conditions
   */
  conditions: GuardrailCondition[];
}

/**
 * Guardrail action config
 */
export interface GuardrailActionConfig {
  /**
   * Message to display
   */
  message?: string | null;

  /**
   * Allow proceeding after warning
   */
  allow_proceed?: boolean | null;

  /**
   * Field to drop
   */
  drop_field?: string | null;

  /**
   * Item to drop
   */
  drop_item?: Record<string, unknown> | null;
}

/**
 * Guardrail action
 */
export interface GuardrailAction {
  /**
   * Action type (block/warn/modify)
   */
  type: string;

  /**
   * Execution priority
   */
  priority: number;

  /**
   * Action configuration
   */
  config: GuardrailActionConfig;
}

/**
 * Guardrail metadata
 */
export interface GuardrailMetadata {
  /**
   * Human-readable description
   */
  description: string;

  /**
   * Tags for categorization
   */
  tags: string[];

  /**
   * Severity level (low/medium/high/critical)
   */
  severity: string;
}

/**
 * Guardrail definition
 */
export interface GuardrailDefinition {
  /**
   * Definition version
   */
  version: string;

  /**
   * Schema version
   */
  schema_version: string;

  /**
   * Trigger conditions
   */
  trigger: GuardrailTrigger;

  /**
   * Actions to execute
   */
  actions: GuardrailAction[];

  /**
   * Metadata
   */
  metadata?: GuardrailMetadata | null;
}

/**
 * Tool invocation rule
 */
export interface ToolInvocationRule {
  /**
   * Name of the tool to invoke
   */
  tool_name: string;

  /**
   * Condition under which this tool should be invoked
   */
  condition: string;

  /**
   * Expected parameter values (natural language)
   */
  parameters: Record<string, string>;

  /**
   * Reasoning for why this tool should be invoked
   */
  reasoning: string;

  /**
   * Guardrail definition with trigger and actions
   */
  guardrail_definition?: GuardrailDefinition | null;
}

/**
 * Drift detection information
 */
export interface DriftDetection {
  /**
   * Reason for drift detection
   */
  reason: string;

  /**
   * Total invocations across all tools
   */
  total_invocations: number;

  /**
   * Invocation count for this specific tool
   */
  tool_invocation_count: number;

  /**
   * Threshold value for drift detection
   */
  threshold: number;

  /**
   * Threshold percentage (e.g., 1.0 for 1%)
   */
  threshold_percent: number;

  /**
   * Minimum total invocations required for drift detection
   */
  min_total_invocations: number;
}

/**
 * Triggered guardrail result
 */
export interface TriggeredGuardrail {
  guardrail_id: string;
  guardrail_name: string;
  triggered: boolean;
  error: boolean;
  error_message: string | null;
  matched_conditions: number[];
  actions: unknown[];
}

/**
 * Evaluation metadata
 */
export interface EvaluationMetadata {
  evaluation_time_ms: number;
  evaluated_guardrails_count: number;
  triggered_guardrails_count: number;
}

/**
 * Evaluation result
 */
export interface EvaluationResult {
  metadata: EvaluationMetadata;
  triggered_guardrails: TriggeredGuardrail[];
}

/**
 * Request context with input/output
 */
export interface RequestContext {
  input: Record<string, unknown>;
  output?: Record<string, unknown>;
}

/**
 * Validation history entry
 */
export interface ValidationHistoryEntry {
  timestamp: string;
  timing: string;
  process_name: string;
  process_type: string;
  should_proceed: boolean;
  request_context: RequestContext;
  evaluation_result: EvaluationResult;
}

/**
 * Inference result
 */
export interface InferenceResult {
  /**
   * Original user instruction
   */
  user_instruction: string;

  /**
   * Ambiguous terms requiring clarification
   */
  ambiguous_terms: Term[];

  /**
   * Resolved terms with interpretations
   */
  resolved_terms: ResolvedTerm[];
}

/**
 * User instruction history item
 */
export interface UserInstructionHistoryItem {
  /**
   * User instruction text
   */
  user_instruction: string;

  /**
   * Timestamp when instruction was recorded (ISO 8601)
   */
  created_at: string;
}

/**
 * Complete session data
 */
export interface SessionData {
  /**
   * Inference result containing user instruction and terms
   */
  inference_result: InferenceResult;

  /**
   * Tool invocation rules generated for this session
   */
  validation_rules: ToolInvocationRule[];

  /**
   * Validation history entries
   */
  validation_history: ValidationHistoryEntry[];

  /**
   * History of user instructions in this session
   */
  user_instruction_history: UserInstructionHistoryItem[];

  /**
   * Tools that are automatically blocked
   */
  disallowed_tools: string[];

  /**
   * Session creation timestamp (ISO 8601)
   */
  created_at: string;

  /**
   * Last update timestamp (ISO 8601)
   */
  updated_at: string;
}
