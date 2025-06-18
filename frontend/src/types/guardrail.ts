export interface TriggerCondition {
  type: 'always' | 'specific_tool' | 'tool_regex';
  tool_name?: string;
  tool_regex?: string;
}

export interface CheckConfig {
  type: 'missing_values_any' | 'missing_values_column' | 'old_date_records';
  target_column?: string;
  date_threshold_days?: number;
}

export interface GuardrailAction {
  type: 'filter_records' | 'interrupt_agent';
}

export interface Guardrail {
  id: string;
  project_id: string;
  name: string;
  description?: string;
  trigger_condition: TriggerCondition;
  check_config: CheckConfig;
  action: GuardrailAction;
  is_active: boolean;
  execution_count: number;
  applied_count: number;
  created_at: string;
  updated_at: string;
}

export interface GuardrailFormData {
  name: string;
  description?: string;
  triggerType: 'always' | 'specific_tool' | 'tool_regex';
  toolName?: string;
  toolRegex?: string;
  checkType: 'missing_values_any' | 'missing_values_column' | 'old_date_records';
  targetColumn?: string;
  dateThresholdDays?: number;
  actionType: 'filter_records' | 'interrupt_agent';
}

export interface GuardrailCreateRequest {
  name: string;
  description?: string;
  trigger_condition: TriggerCondition;
  check_config: CheckConfig;
  action: GuardrailAction;
  is_active: boolean;
}