export interface QualityIssue {
  observation_id: string;
  column?: string;
  quality_metrics: string;
  issue_type: string;
  severity: 'low' | 'medium' | 'high';
  description: string;
  metadata?: any;
  timestamp: string;
}

export interface Trace {
  id: string;
  project_id: string;
  external_id: string;
  platform_type: 'langfuse';
  timestamp: string;
  raw_data: Record<string, any>;
  quality_score?: number;
  quality_issues?: QualityIssue[];
  observations?: Observation[];
  last_synced_at: string;
  created_at: string;
  updated_at: string;
}

export interface Observation {
  id: string;
  trace_id: string;
  parent_observation_id?: string;
  external_id: string;
  platform_type: 'langfuse';
  start_time: string;
  raw_data: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface TraceSyncStatus {
  project_id: string;
  total_traces: number;
  new_traces: number;
  updated_traces: number;
  sync_started_at: string;
  sync_completed_at?: string;
  error?: string;
}

export interface TraceListResponse {
  traces: Trace[];
  total: number;
  page: number;
  limit: number;
}