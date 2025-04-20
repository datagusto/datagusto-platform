// Define a type for observations
export type Observation = {
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
};

// Define a type for traces
export type Trace = {
  id: string;
  agent_id: string;
  name?: string;
  input?: string;
  output?: string;
  trace_metadata?: Record<string, unknown>;
  timestamp?: string;
  created_at: string;
  updated_at?: string;
  observability_id?: string;
  status: "IN_PROGRESS" | "COMPLETED" | "ERROR";
  latency?: number;
  total_cost?: number;
  evaluation_results?: {
    root_cause?: {
      number_of_issues: number;
      description?: string;
    }
  };
}; 