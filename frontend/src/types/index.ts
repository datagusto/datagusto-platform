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
  user_query: string;
  final_response: string | null;
  started_at: string;
  completed_at: string | null;
  status: "IN_PROGRESS" | "COMPLETED" | "ERROR";
  trace_metadata: Record<string, unknown>;
  latency_ms: number | null;
  total_tokens: number | null;
  cost: number | null;
}; 