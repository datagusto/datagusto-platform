import { Trace, TraceSyncStatus, TraceListResponse } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_VERSION = process.env.NEXT_PUBLIC_API_VERSION || 'v1';

export class TraceService {
  private static getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  }

  /**
   * Get traces for a specific project
   */
  static async getTracesByProject(
    projectId: string,
    options: {
      limit?: number;
      offset?: number;
    } = {}
  ): Promise<TraceListResponse> {
    const { limit = 50, offset = 0 } = options;
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });

    const response = await fetch(
      `${API_BASE_URL}/api/${API_VERSION}/traces/${projectId}?${params}`,
      {
        method: 'GET',
        headers: this.getAuthHeaders(),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch traces: ${response.statusText}`);
    }

    const traces = await response.json();
    return {
      traces,
      total: traces.length,
      page: Math.floor(offset / limit) + 1,
      limit,
    };
  }

  /**
   * Get a single trace with observations
   */
  static async getTraceById(projectId: string, traceId: string): Promise<Trace> {
    const response = await fetch(
      `${API_BASE_URL}/api/${API_VERSION}/traces/${projectId}/${traceId}`,
      {
        method: 'GET',
        headers: this.getAuthHeaders(),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch trace: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get observations for a specific trace
   */
  static async getObservations(projectId: string, traceId: string): Promise<any[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/${API_VERSION}/traces/${projectId}/${traceId}/observations`,
      {
        method: 'GET',
        headers: this.getAuthHeaders(),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch observations: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Sync traces from external platform (e.g., Langfuse)
   */
  static async syncTraces(projectId: string): Promise<TraceSyncStatus> {
    const response = await fetch(
      `${API_BASE_URL}/api/${API_VERSION}/traces/${projectId}/sync`,
      {
        method: 'POST',
        headers: this.getAuthHeaders(),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to sync traces: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Format timestamp for display
   */
  static formatTimestamp(timestamp: string): string {
    return new Date(timestamp).toLocaleString();
  }

  /**
   * Get trace name from raw data
   */
  static getTraceName(trace: Trace): string {
    return trace.raw_data?.name || trace.raw_data?.id || trace.external_id;
  }

  /**
   * Get trace status from raw data
   */
  static getTraceStatus(trace: Trace): string {
    // Check if there are any quality issues, if so, status is "Incident"
    if (trace.quality_issues && trace.quality_issues.length > 0) {
      return 'incident';
    }
    
    return trace.raw_data?.status || 'completed';
  }

  /**
   * Get trace duration from raw data
   */
  static getTraceDuration(trace: Trace): string | null {
    const startTime = trace.raw_data?.startTime;
    const endTime = trace.raw_data?.endTime;
    
    if (!startTime || !endTime) return null;
    
    const start = new Date(startTime);
    const end = new Date(endTime);
    const duration = end.getTime() - start.getTime();
    
    if (duration < 1000) {
      return `${duration}ms`;
    } else {
      return `${(duration / 1000).toFixed(2)}s`;
    }
  }
}