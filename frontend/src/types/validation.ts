export type ValidationRule = {
  id: string;
  name: string;
  description: string;
  criteria: string;
  severityLevel: 'low' | 'medium' | 'high' | 'critical';
};

export type ValidationResult = {
  ruleId: string;
  ruleName: string;
  passed: boolean;
  score: number;
  details: string;
};

// Extend the Observation type with validation results
export type ObservationWithValidation = {
  id: string;
  traceId: string;
  parentObservationId: string | null;
  type: string;
  name: string;
  startTime: string;
  endTime: string;
  duration: string;
  input: string | Record<string, unknown> | null;
  output: string | Record<string, unknown> | null;
  level: string;
  statusCode: number;
  metadata: Record<string, unknown>;
  validationResults?: ValidationResult[];
  quality: 'Good' | 'Average' | 'Poor';
}; 